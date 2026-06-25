import sqlite3
import pandas as pd

# Load CSV
df = pd.read_csv("transaction_vietnam_100k_part_1.csv")

# Kết nối SQLite và tạo bảng
conn = sqlite3.connect("demo.db")
cursor = conn.cursor()

# Tạo bảng (thay đổi kiểu dữ liệu nếu cần)
cursor.execute("""
DROP TABLE IF EXISTS transaction_vietnam_100k_part_1;
""")
cursor.execute("""
CREATE TABLE transaction_vietnam_100k_part_1 (
    customer_id INTEGER,
    date_of_birth TEXT,
    email TEXT,
    gender TEXT,
    phone TEXT
)
""")

# Ghi dữ liệu vào bảng
df.to_sql("transaction_vietnam_100k_part_1", conn, if_exists='append', index=False)

conn.commit()
conn.close()

print("✅ SQLite DB created: demo.db")



