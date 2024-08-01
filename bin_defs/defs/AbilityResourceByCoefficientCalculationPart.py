from ..bin_calc import *

class AbilityResourceByCoefficientCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')
        if stat_formula:
            icon_modifier = self.get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

        value = current_block['mCoefficient']
        try:
            value = float(value) * 100
        except:
            pass

        placeholders = {
            '@IconModifier@': icon_modifier,
            '@OpeningTag@': '<scalemana>',
            '@Icon@': '%i:scaleMana%',
            '@ClosingTag@': '</scalemana>',
            '@Value@': round_number(value, 5)
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0