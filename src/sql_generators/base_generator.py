import re

class BaseSqlGenerator:
    def _parse_pointer(self, pointer_string: str) -> tuple[str, str, str]:
        parts = pointer_string.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid 'pointer' format: {pointer_string}. Must be 'schema.table.column'.")
        return parts[0], parts[1], parts[2]

    def _build_select_clause(self, select_columns: list, alias: str = None) -> str:
        if not select_columns:
            return ""
        
        prefix = f"{self._sanitize_sql_identifier(alias)}." if alias else ""
        sanitized_cols = [f"{prefix}{self._sanitize_sql_identifier(col)}" for col in select_columns]
        
        return ', '.join(sanitized_cols) + ','
    def _build_calculation_expression(self, columns: list[str], keyword: str = "") -> str:
        if not columns:
            raise ValueError("Column list cannot be empty for calculation.")

        sanitized_cols = [self._sanitize_sql_identifier(c) for c in columns]
        inner_expr = f"({ ' + '.join(sanitized_cols) })" if len(sanitized_cols) > 1 else sanitized_cols[0]

        if keyword:
            sanitized_keyword = self._sanitize_sql_identifier(keyword.upper())
            return f"{sanitized_keyword}({inner_expr})"
        else:
            return inner_expr
    def _sanitize_sql_identifier(self, identifier: str) -> str:
        if not identifier:
            return ""
        if not re.fullmatch(r'[a-zA-Z0-9_.]+', identifier):
            raise ValueError(f"Invalid SQL identifier or potential SQL Injection: {identifier}")
        return identifier

    def _format_sql_value(self, value) -> str:
        if isinstance(value, str):
            return f"'{value.replace("'", "''")}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif isinstance(value, list):
            return f"({', '.join([self._format_sql_value(item) for item in value])})"
        elif value is None:
            return "NULL"
        raise ValueError(f"Unsupported data type for SQL formatting: {type(value)}")

    def generate_sql(self, rule_definition: dict) -> str:
        raise NotImplementedError("This method must be implemented by a subclass.")
    
    def generate_condition_sql(self, rule_definition: dict) -> str:
        raise NotImplementedError("This method must be implemented by a subclass.")
