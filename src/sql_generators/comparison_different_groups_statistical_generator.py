from .base_generator import BaseSqlGenerator

class ComparisonDifferentGroupsStatisticalGenerator(BaseSqlGenerator):
    
    def generate_condition_sql(self, rule_definition: dict) -> str:
        raise NotImplementedError("Comparison rules cannot be used as sub-rules in a complex rule.")

    def generate_sql(self, rule: dict) -> str:
        op = rule['comparison_operator']
        
        negated_op = {
            '=': '!=',
            '!=': '=',
            '>': '<=',
            '<': '>=',
            '>=': '<',
            '<=': '>'
        }.get(op, f'NOT {op}')

        join_columns = rule['join_columns']
        calc_1_def = rule['calculation_1']
        calc_2_def = rule['calculation_2']
        select_columns = rule.get('select_columns', [])

        table_1 = self._sanitize_sql_identifier(calc_1_def['table'])
        table_2 = self._sanitize_sql_identifier(calc_2_def['table'])
        
        join_conditions = ' AND '.join(
            f"T1.{self._sanitize_sql_identifier(col)} = T2.{self._sanitize_sql_identifier(col)}" for col in join_columns
        )
        
        select_clause_str = self._build_select_clause(select_columns, 'T1')
        
        group_by_items = [f"T1.{self._sanitize_sql_identifier(col)}" for col in select_columns]
        group_by_items += [f"T1.{self._sanitize_sql_identifier(col)}" for col in join_columns]
        if not calc_2_def.get('keyword'):
            for col in calc_2_def['columns']:
                group_by_items.append(f"T2.{self._sanitize_sql_identifier(col)}")
        group_by_clause_str = ", ".join(sorted(list(set(group_by_items))))

        calc_expr_1_body = self._build_calculation_expression([f"T1.{c}" for c in calc_1_def['columns']], calc_1_def.get('keyword', ''))
        calc_expr_2_body = self._build_calculation_expression([f"T2.{c}" for c in calc_2_def['columns']], calc_2_def.get('keyword', ''))
        
        return f"""
SELECT
    {select_clause_str}
    {', '.join(f'T1.{self._sanitize_sql_identifier(col)}' for col in join_columns)},
    {calc_expr_1_body} AS calculated_value_1,
    {calc_expr_2_body} AS calculated_value_2,
    CASE
        WHEN {calc_expr_1_body} {op} {calc_expr_2_body} THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status,
    '{rule['rule_id']}' AS rule_id
FROM
    {table_1} T1
JOIN
    {table_2} T2 ON {join_conditions}
GROUP BY
    {group_by_clause_str};
""".strip()
