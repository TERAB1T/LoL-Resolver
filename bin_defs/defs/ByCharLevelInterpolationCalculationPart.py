from ..bin_calc import *

class ByCharLevelInterpolationCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        if 'mStartValue' not in current_block:
            return getf(current_block, 'mEndValue', '0')

        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.get_string(formula_part_style_key)

        placeholders = {
            '@OpeningTag@': '<scaleLevel>',
            '@RangeStart@': round_number(float(current_block['mStartValue']), 5),
            '@RangeEnd@': round_number(float(current_block['mEndValue']), 5),
            '@Icon@': '%i:scaleLevel%',
            '@ClosingTag@': '</scaleLevel>'
        }

        for placeholder, value in placeholders.items():
            return_value = str_ireplace(placeholder, value, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0