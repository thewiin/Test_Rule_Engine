import decimal
import uuid
import traceback
from flask import Flask, Response, request, jsonify
import json
import os 
import io, csv
from datetime import datetime, timezone
from src.sql_generator import SqlGenerator
from src.rule_parser import RuleParser

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor 

from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from flask.json.provider import JSONProvider

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, default=self.default)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

    @staticmethod
    def default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

load_dotenv()
app = Flask(__name__, template_folder='templates', static_folder='static')
app.json = CustomJSONProvider(app) 
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000"]}})

conn = None
engine = SqlGenerator()
parser = RuleParser()

def connectDatabase():
    global conn
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env file")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False 
        with conn.cursor() as cur:
            all_schemas = "public, customer_data, bank_data, loans, core, staging, transactions, sales, transactions_schema"
            cur.execute(f"SET search_path TO {all_schemas}")
            conn.commit()
        print("✅ Successfully connected to Database Server and set search_path!")
    except psycopg2.OperationalError as e:
        print(f"The error '{e}' occurred")
        raise

@app.route('/', methods=['GET'])
def index():
    return render_template('front-end.html') 

@app.route('/api/upload-rule', methods=['POST'])
def upload_rule():
    rule = request.get_json()
    if not rule or not rule.get("rule_id"):
        return jsonify({"status": "error", "message": "Invalid JSON or missing rule_id"}), 400
    rule_id = rule.get("rule_id")
    definition_json = json.dumps(rule)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO rule_definitions (rule_id, definition) VALUES (%s, %s) ON CONFLICT (rule_id) DO UPDATE SET definition = EXCLUDED.definition",
                (rule_id, definition_json)
            )
            conn.commit()
        return jsonify({"status": "success", "message": f"Rule '{rule_id}' saved."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/validate-rule', methods=['POST'])
def validate_rule():
    try:
        rule = request.get_json()
        parsed_rule = parser.parse_rule_from_dict(rule)
        sql = engine.generate_sql(parsed_rule)
        return jsonify({"sql": sql})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/run-rule", methods=["POST"])
def execute_sql():
    request_data = request.get_json()
    if not request_data:
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    sql_query = request_data.get('sql_query')
    rule = request_data.get('rule') 

    if not sql_query:
        return jsonify({"status": "error", "message": "Request payload must contain a non-empty 'sql_query' field."}), 400
    
    execution_id = str(uuid.uuid4())
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql_query)
            results = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            
            all_rows = [dict(zip(colnames, row)) for row in results]
            
            total_rows_checked = len(all_rows)

            violating_rows = [row for row in all_rows if row.get('validation_status') == 'FAILED']
            
            cur.execute(
                "INSERT INTO execution_results (id, status, created_at, total_rows_checked) VALUES (%s, 'RUNNING', %s, %s)",
                (execution_id, datetime.now(timezone.utc), total_rows_checked)
            )
            conn.commit()

            result_data = {
                "rowCount": len(violating_rows), 
                "headers": colnames,
                "rows": all_rows 
            }

            cur.execute(
                "UPDATE execution_results SET status = 'COMPLETED', result_data = %s, completed_at = %s WHERE id = %s",
                (app.json.dumps(result_data), datetime.now(timezone.utc), execution_id)
            )
            conn.commit()
            
        return jsonify({"status": "success", "executionId": execution_id}), 202
    
    except psycopg2.Error as db_err:
        conn.rollback()
        print("--- DATABASE ERROR TRACEBACK ---")
        traceback.print_exc()
        print("---------------------------------")
        if 'execution_id' in locals():
            with conn.cursor() as cur:
                cur.execute("UPDATE execution_results SET status = 'FAILED', error_message = %s, completed_at = %s WHERE id = %s", (str(db_err), datetime.now(timezone.utc), execution_id))
                conn.commit()
        return jsonify({"status": "error", "message": f"Database error: {db_err}"}), 500
    
    except Exception as e:
        conn.rollback()
        print("--- GENERAL ERROR TRACEBACK ---")
        traceback.print_exc()
        print("---------------------------------")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-result', methods=['GET'])
def get_result():
    execution_id = request.args.get('rule_id')
    if not execution_id:
        return jsonify({"status": "error", "message": "Missing rule_id"}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM execution_results WHERE id = %s", (execution_id,))
            result = cur.fetchone()
        if not result:
            return jsonify({"status": "error", "message": "Execution ID not found"}), 404
        
        db_status = result['status']
        response_data = {}

        if db_status == 'COMPLETED':
            total_checked = result.get('total_rows_checked', 0)
            result_json = result.get('result_data', {'rowCount': 0})
            violations = result_json.get('rowCount', 0)
            
            total_passed = (total_checked - violations) if total_checked >= violations else 0

            response_data['status'] = 'FAIL' if violations > 0 else 'PASS'
            response_data['total_passed'] = total_passed
            response_data['violations'] = violations 
            response_data['records'] = result_json.get('rows', []) 
            response_data['download_link'] = url_for('download_result', execution_id=execution_id)
        
        elif db_status == 'FAILED':
            response_data['status'] = 'FAIL'
            response_data['message'] = result.get('error_message', 'Unknown error')
        else: 
            response_data['status'] = 'RUNNING'
            
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/download/result/<string:execution_id>', methods=['GET'])
def download_result(execution_id):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT result_data FROM execution_results WHERE id = %s", (execution_id,))
            result = cur.fetchone()

        if not result or not result['result_data'] or not result['result_data'].get('rows'):
            return jsonify({"error": "No violation records to export."}), 404

        records = result['result_data']['rows']

        if not records:
             return "No violation records to export.", 200

        output = io.StringIO()
        headers = records[0].keys()
        writer = csv.DictWriter(output, fieldnames=headers)

        writer.writeheader()
        writer.writerows(records)

        csv_output = output.getvalue()

        return Response(
            csv_output,
            mimetype="text/csv",
            headers={"Content-disposition":
                     f"attachment; filename=result_{execution_id}.csv"}
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to generate CSV file.", "details": str(e)}), 500

if __name__ == '__main__':
    try:
        connectDatabase()
        app.run(debug=True, host='0.0.0.0', port=5000)
    except (ValueError, psycopg2.OperationalError) as e:
        print(f"Could not start the application. Error: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed.")