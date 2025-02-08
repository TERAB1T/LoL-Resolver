from ..bin_calc import *

class ByCharLevelBreakpointsCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.get_string(formula_part_style_key)

        level1_value = current_block.get('mLevel1Value', 0)
        initial_bonus_per_level = getf(current_block, 'mInitialBonusPerLevel')
        range_end = level1_value

        if 'mBreakpoints' in current_block:
            last_level = 18
            end_value = level1_value

            for m_breakpoint in reversed(current_block['mBreakpoints']):
                m_level = getf(m_breakpoint, 'mLevel', 0)

                if m_level > last_level:
                    continue
                
                if getf(m_breakpoint, 'mAdditionalBonusAtThisLevel'):
                    current_value = getf(m_breakpoint, 'mAdditionalBonusAtThisLevel')
                    diff = last_level - m_level + 1
                    end_value += current_value
                    last_level -= diff
                else:
                    current_value = getf(m_breakpoint, 'mBonusPerLevelAtAndAfter', 0)
                    diff = last_level - m_level + 1
                    end_value += diff * current_value
                    last_level -= diff

            if last_level > 0 and initial_bonus_per_level:
                diff = last_level - 1
                end_value += diff * initial_bonus_per_level

            range_end = round_number(end_value, 5)

        if initial_bonus_per_level and level1_value == range_end:
            range_end = round_number(initial_bonus_per_level * 17 + level1_value, 5)
        
        if level1_value == range_end:
            return round_number(float(level1_value), 5)

        placeholders = {
            '@OpeningTag@': '<scaleLevel>',
            '@RangeStart@': round_number(float(level1_value), 5, True),
            '@Icon@': '%i:scaleLevel%',
            '@RangeEnd@': round_number(float(range_end), 5, True),
            '@ClosingTag@': '</scaleLevel>'
        }

        for placeholder, replacement in placeholders.items():
            return_value = re.sub(placeholder, replacement, return_value, flags=re.IGNORECASE)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0