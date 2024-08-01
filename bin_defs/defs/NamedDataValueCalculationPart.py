from ..bin_calc import *

class NamedDataValueCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstyle" if key == 0 else "tooltip_statsuidata_formulapartstylebonus"
        return_value = self.get_string(formula_part_style_key)

        value = self.var_values.get(current_block['mDataValue'].lower(), 0)
        formatted_value = round_number(value, 5) if isinstance(value, (int, float)) else 0

        placeholders = {
            '@OpeningTag@': '',
            '@IconModifier@': '',
            '@Icon@': '',
            '@ClosingTag@': '',
            '@Value@': formatted_value
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstyle" if key == 0 else "tooltip_statsuidata_formulapartstylebonus"
        return_value = self.get_string(formula_part_style_key)

        value = self.var_values.get(current_block['mDataValue'].lower(), 0)
        formatted_value = round_number(value, 5) if isinstance(value, (int, float)) else 0

        placeholders = {
            '@OpeningTag@': '',
            '@IconModifier@': '',
            '@Icon@': '',
            '@ClosingTag@': '',
            '@Value@': formatted_value
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value