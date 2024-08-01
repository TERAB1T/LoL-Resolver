from ..bin_calc import *

class BuffCounterByNamedDataValueCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)

        icon = getf(current_block, 'mIconKey', '')
        value = self.var_values.get(getf(current_block, 'mDataValue').lower(), 0)

        placeholders = {
            '@IconModifier@': '',
            '@OpeningTag@': '',
            '@Icon@': icon,
            '@ClosingTag@': '',
            '@Value@': round_number(value * 100, 5)
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0