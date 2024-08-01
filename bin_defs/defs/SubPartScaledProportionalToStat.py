from ..bin_calc import *

class SubPartScaledProportionalToStat(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)
        
        current_subpart = self.check_dict(self.calc_values(current_block['mSubpart']))
        current_stat = round_number(current_block.get('mStat', 0), 5)
        current_ratio = round_number(current_block.get('mRatio', 1) * 100, 5)

        placeholders = {
            '@IconModifier@': '',
            '@OpeningTag@': stats[current_stat]['openingTag'],
            '@Icon@': stats[current_stat]['icon'],
            '@ClosingTag@': stats[current_stat]['closingTag'],
            '@Value@': round_number(current_subpart * current_ratio, 5)
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        current_stat = self.champion_stats[current_block.get('mStat', 0)]
        current_ratio = current_block.get('mRatio', 1)
        current_value = self.check_dict(self.calc_values(current_block['mSubpart'], 0, 'float'))
        current_value = float(current_value)

        current_tag = getf(current_block, 'mStyleTag')
        current_icon = getf(current_block, 'mStyleTagIfScaled')

        if current_icon == 'noScale' and current_tag != 'noScale':
            current_icon, current_tag = current_tag, current_icon

        if current_tag and current_icon:
            return {
                'value': current_stat * current_ratio * current_value,
                'tag': current_tag,
                'icon': current_icon
            }
        
        return current_stat * current_ratio * current_value