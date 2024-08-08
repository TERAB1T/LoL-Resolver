from ..bin_calc import *

class BuffCounterByCoefficientCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        m_icon_key = getf(current_block, 'mIconKey')
        m_scaling_tag_key = getf(current_block, 'mScalingTagKey')
        m_coefficient = getf(current_block, 'mCoefficient', 1.0)

        if not m_icon_key:
            return 0
        
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.get_string(formula_part_style_key)

        opening_tag = ''
        closing_tag = ''

        if m_scaling_tag_key:
            opening_tag = f'<{m_scaling_tag_key}>'
            closing_tag = f'</{m_scaling_tag_key.split(" ")[0]}>'

        placeholders = {
            '@OpeningTag@': opening_tag,
            '@IconModifier@': '',
            '@Icon@': m_icon_key,
            '@ClosingTag@': closing_tag,
            '@Value@': round_number(m_coefficient * 100, 5)
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0