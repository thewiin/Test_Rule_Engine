from .base_generator import BaseSqlGenerator

class ComplexBooleanRuleSqlGenerator(BaseSqlGenerator):
    def generate_condition_sql(self, rule_definition: dict) -> str:
        raise NotImplementedError("A complex rule cannot be a sub-rule of another complex rule.")

    def generate_sql(self, rule: dict) -> str:
        from src.sql_generator import SqlGenerator
        sql_generator = SqlGenerator()

        boolean_expression = rule['boolean_expression']
        sub_rules = rule['sub_rules_definitions']

        if not sub_rules:
            raise ValueError("Complex rule must have at least one sub-rule.")

        first_sub_rule = sub_rules[0]
        if 'pointer' not in first_sub_rule:
            raise ValueError("Sub-rules within a complex rule must have a 'pointer' to determine the primary table.")
        
        schema, table, _ = self._parse_pointer(first_sub_rule['pointer'])
        primary_table = f"{self._sanitize_sql_identifier(schema)}.{self._sanitize_sql_identifier(table)}"

        conditions = {}
        for sub_rule in sub_rules:
            sub_rule_id = sub_rule['rule_id']
            rule_type = sub_rule['rule_type']
            
            generator = sql_generator.generators.get(rule_type)
            if not generator:
                raise NotImplementedError(f"SQL generation for sub-rule type '{rule_type}' is not implemented.")
            
            condition_sql = generator.generate_condition_sql(sub_rule)
            conditions[sub_rule_id] = condition_sql
        
        final_condition = f" {boolean_expression} "
        for rule_id, condition in conditions.items():
            final_condition = final_condition.replace(f" {rule_id} ", f" ({condition}) ")

        final_condition = final_condition.strip()
        
        select_clause = self._build_select_clause(rule.get('select_columns'))

        return f"""
SELECT
    {select_clause}
    CASE
        WHEN {final_condition} THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status,
    '{rule['rule_id']}' AS rule_id
FROM
    {primary_table};
""".strip()
