from ..bin_calc import *

class StatBySubPartCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)

        current_stat = current_block.get('mStat', 0)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')

        if stat_formula:
            icon_modifier = self.get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

        value = self.check_dict(self.calc_values(current_block['mSubpart'], key))

        try:
            value = float(value) * 100
        except:
            pass

        placeholders = {
            '@IconModifier@': icon_modifier,
            '@OpeningTag@': stats[current_stat]['openingTag'],
            '@Icon@': stats[current_stat]['icon'],
            '@ClosingTag@': stats[current_stat]['closingTag'],
            '@Value@': round_number(value, 5)
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        current_stat = self.champion_stats[current_block.get('mStat', 0)]
        current_value = self.check_dict(self.calc_values(current_block['mSubpart'], 0, 'float'))
        current_value = float(current_value)

        stat_formula = current_block.get('mStatFormula', 1)

        if stat_formula == 2:
            return 0

        return current_stat * current_value