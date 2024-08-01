from ..bin_calc import *

class ByCharLevelFormulaCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        m_values = getf(current_block, 'mValues', [0] * 18)
        start_value = m_values[1]
        end_value = m_values[18]

        if not start_value:
            start_value = 0

        if not end_value:
            end_value = m_values[len(m_values) - 1]

        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.get_string(formula_part_style_key)

        placeholders = {
            '@OpeningTag@': '<scaleLevel>',
            '@RangeStart@': round_number(float(start_value), 5),
            '@RangeEnd@': round_number(float(end_value), 5),
            '@Icon@': '%i:scaleLevel%',
            '@ClosingTag@': '</scaleLevel>'
        }

        for placeholder, value in placeholders.items():
            return_value = str_ireplace(placeholder, value, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0