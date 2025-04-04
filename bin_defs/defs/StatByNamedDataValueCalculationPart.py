from ..bin_calc import *

class StatByNamedDataValueCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)

        current_stat = current_block.get('mStat', 0)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')

        if stat_formula:
            icon_modifier = self.get_string(f'tooltip_statsuidata_{STAT_TYPES[stat_formula]}iconmodifier')

        value = self.var_values.get(current_block['mDataValue'].lower())

        try:
            value = float(value) * 100
        except:
            pass

        placeholders = {
            '@IconModifier@': icon_modifier,
            '@OpeningTag@': STATS[current_stat]['openingTag'],
            '@Icon@': STATS[current_stat]['icon'],
            '@ClosingTag@': STATS[current_stat]['closingTag'],
            '@Value@': round_number(value, 5, True)
        }
        
        if value is None:
            return 0

        for placeholder, replacement in placeholders.items():
            return_value = re.sub(placeholder, replacement, return_value, flags=re.IGNORECASE)

        return return_value
    
    def calc_float(self, current_block, key):
        stat_type = current_block.get('mStat', 0)
        current_stat = self.champion_stats[stat_type]
        current_value = self.var_values.get(current_block['mDataValue'].lower(), 0)
        stat_formula = current_block.get('mStatFormula', 1)

        if stat_formula == 2:
            return 0
        
        return {
            'value': current_stat * current_value,
            'tag': re.sub(r'[<>]', '', STATS[stat_type]['openingTag']),
            'icon': re.sub(r'%i:(.*?)%', '\\1', STATS[stat_type]['icon'])
        }