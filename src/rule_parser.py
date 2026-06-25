import json
import os

class RuleParser:

    def __init__(self):
        pass
    
    def parse_pointer(self, pointer: str) -> tuple[str, str, str]:
        if not isinstance(pointer, str) or len(pointer.split('.')) != 3:
            raise ValueError(f"Invalid 'pointer' format (must be 'schema.table.column'): {pointer}")
        schema, table, column = pointer.split('.')
        return schema, table, column

    def parse_rule_from_dict(self, rule_dict: dict) -> dict:
        try:
            self._validate_basic_rule_structure(rule_dict)
            return rule_dict
        except ValueError as e:
            raise ValueError(f"Invalid rule dictionary: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while parsing the rule dictionary: {e}")
        
    def parse_rule_from_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Rule file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_definition = json.load(f)
            self._validate_basic_rule_structure(rule_definition)
            return rule_definition
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing error in file {file_path}: {e}")
        except ValueError as e:
            raise e 
        except Exception as e:
            raise Exception(f"Unknown error reading rule file {file_path}: {e}")

    def _validate_basic_rule_structure(self, rule: dict):
        if "rule_type" not in rule:
            raise ValueError("Rule definition is missing required field: 'rule_type'.")

        if "rule_id" not in rule and "complex_rule_id" not in rule:
             raise ValueError("Rule definition is missing required field: 'rule_id' or 'complex_rule_id'.")

        common_required_fields = ["rule_name", "description"]
        for field in common_required_fields:
            if field not in rule:
                raise ValueError(f"Rule definition is missing common required field: '{field}'.")

        rule_type = rule["rule_type"]
        
        type_specific_fields = {
            "VALUE_RANGE": ["pointer", "min_value", "max_value"],
            "VALUE_TEMPLATE": ["pointer", "template_regex"],
            "DATA_CONTINUITY_INTEGRITY": ["pointer", "partition_by_column", "order_by_column"],
            "COMPARISON_SAME_GROUPS_STATISTICAL": ["pointers_1", "pointers_2", "join_columns"],
            "COMPARISON_DIFFERENT_GROUPS_STATISTICAL": ["calculation_1", "calculation_2", "join_columns"],
            "COMPLEX_BOOLEAN_RULE": ["boolean_expression", "sub_rules_definitions"]
        }

        required_fields = type_specific_fields.get(rule_type)

        if required_fields is None:
            raise ValueError(f"Invalid or unsupported rule type: '{rule_type}'.")

        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Rule definition of type '{rule_type}' is missing required field: '{field}'.")

        if "pointer" in rule:
            self.parse_pointer(rule["pointer"])
