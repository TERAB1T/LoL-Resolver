from utils import *
from stats import *

class BinDefinitions:
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}, needs_calculation = False):
        self.strings_raw = strings
        self.var_values = var_values
        self.all_calculations = all_calculations
        self.champion_stats = champion_stats
        self.needs_calculation = needs_calculation

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __check_dict(self, value):
        if isinstance(value, dict) and 'icon' in value:
            value = value['value']
        
        return value
    
    def parse_values(self, current_block, key=0):
        if not isinstance(current_block, (list, dict)):
            return current_block
        
        block_type = current_block['__type']

        known_types = [
            'GameCalculation',
            'GameCalculationConditional',
            'ByCharLevelInterpolationCalculationPart',
            'NamedDataValueCalculationPart',
            'NumberCalculationPart',
            'EffectValueCalculationPart',
            'AbilityResourceByCoefficientCalculationPart',
            'ByCharLevelBreakpointsCalculationPart',
            'ByCharLevelFormulaCalculationPart',
            'ProductOfSubPartsCalculationPart',
            'SumOfSubPartsCalculationPart',
            'GameCalculationModified',
            'StatByNamedDataValueCalculationPart',
            'StatByCoefficientCalculationPart',
            'StatBySubPartCalculationPart',
            '{f3cbe7b2}',
            'ClampSubPartsCalculationPart',
            'StatEfficiencyPerHundred',
            '{e9a3c91d}',
            '{4750ceb6}',
            'SubPartScaledProportionalToStat'
            ]

        if block_type in known_types:
            return getattr(self, f'_BinDefinitions__{block_type.strip("{}")}')(current_block, key)
        elif block_type in [
            'BuffCounterByCoefficientCalculationPart',
            'BuffCounterByNamedDataValueCalculationPart',
            'ByItemEpicnessCountCalculationPart'
            ]:
            return 0
        else:
            for current_type in known_types:
                if block_type == hash_fnv1a(current_type):
                    return getattr(self, f'_BinDefinitions__{current_type.strip("{}")}')(current_block, key)

            return '@CalcError@' #current_block
    
    def __GameCalculation(self, current_block, key=0):
        m_formula_parts = []
        calculated_tag = None
        calculated_icon = None

        for i, value in enumerate(current_block['mFormulaParts']):
            if self.needs_calculation:
                block_calculation = self.parse_values(value, i)

                if isinstance(block_calculation, dict):
                    calculated_value = block_calculation['value']
                    calculated_tag = block_calculation['tag']
                    calculated_icon = block_calculation['icon']
                else:
                    calculated_value = block_calculation

                m_formula_parts.append(float(round_number(calculated_value, 5, True)))
            else:
                current_value = self.parse_values(value, i)

                if re.match(r'^-?\d*\.?\d*$', str(current_value)):
                    current_value = float(current_value)

                m_formula_parts.append(round_number(current_value, 5))

        if self.needs_calculation:
            return_value = sum(m_formula_parts.values())
        else:
            if all(isinstance(x, (int, float)) for x in m_formula_parts):
                return_value = sum(m_formula_parts)
            else:
                return_value = ' '.join(str(x) for x in m_formula_parts)

        if 'mMultiplier' in current_block:
            def callback_for_multiplier(matches):
                number = float(matches.group(1))
                return round_number(number * mMultiplier, 5, True)
            
            mMultiplier = self.parse_values(current_block['mMultiplier'])

            if not mMultiplier:
                mMultiplier = 1

            try:
                mMultiplier = float(mMultiplier)
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_multiplier, str(return_value))
            except:
                pass

        if 'mDisplayAsPercent' in current_block:
            if isinstance(return_value, (int, float)):
                return_value = str_ireplace('@NUMBER@', round_number(return_value * 100, getf(current_block, 'mPrecision', 5)), self.__get_string('number_formatting_percentage_format'))
            elif '%i:scaleLevel%' in return_value:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return round_number(number * 100, 5, True)
                
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)
                return_value = str_ireplace('@NUMBER@', return_value.split('%i:scaleLevel%')[0], self.__get_string('number_formatting_percentage_format')) + '%i:scaleLevel%' + return_value.split('%i:scaleLevel%')[1]
            else:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return str_ireplace('@NUMBER@', round_number(number * 100, 5, True), self.__get_string('number_formatting_percentage_format'))

                return_value = re.sub(r'^([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)

        if calculated_tag and calculated_icon:
            return {
                'value': return_value,
                'tag': calculated_tag,
                'icon': calculated_icon
            }
        else:
            return return_value
        
    def __GameCalculationConditional(self, current_block, key=0):
        default_game_calculation = getf(current_block, 'mDefaultGameCalculation')
        return self.parse_values(self.all_calculations[default_game_calculation], key)
    
    def __ByCharLevelInterpolationCalculationPart(self, current_block, key=0):
        if 'mStartValue' not in current_block:
            return getf(current_block, 'mEndValue', '0')

        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.__get_string(formula_part_style_key)

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
    
    def __NamedDataValueCalculationPart(self, current_block, key=0):
        if self.needs_calculation:
            return getf(self.var_values, current_block["mDataValue"].lower(), 0)
        
        formula_part_style_key = "tooltip_statsuidata_formulapartstyle" if key == 0 else "tooltip_statsuidata_formulapartstylebonus"
        return_value = self.__get_string(formula_part_style_key)

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
    
    def __NumberCalculationPart(self, current_block, key=0):
        return getf(current_block, 'mNumber', 0)
    
    def __EffectValueCalculationPart(self, current_block, key=0):
        effect_key = f"effect{current_block['mEffectIndex']}amount"
        return self.var_values.get(effect_key, 0)
    
    def __StatByNamedDataValueCalculationPart(self, current_block, key=0):
        if self.needs_calculation:
            stat_type = current_block.get('mStat', 0)
            current_stat = self.champion_stats[stat_type]
            current_value = self.var_values.get(current_block['mDataValue'].lower(), 0)
            stat_formula = current_block.get('mStatFormula', 1)

            if stat_formula == 2:
                return 0
            
            return {
                'value': current_stat * current_value,
                'tag': re.sub(r'[<>]', '', stats[stat_type]['openingTag']),
                'icon': re.sub(r'%i:(.*?)%', '\\1', stats[stat_type]['icon'])
            }

        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.__get_string(formula_part_style_key)

        current_stat = current_block.get('mStat', 0)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')

        if stat_formula:
            icon_modifier = self.__get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

        value = self.var_values.get(current_block['mDataValue'].lower())

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
    
    def __StatByCoefficientCalculationPart(self, current_block, key=0):
        if self.needs_calculation:
            current_stat = self.champion_stats[current_block.get('mStat', 0)]
            current_coef = current_block['mCoefficient']
            stat_formula = current_block.get('mStatFormula', 1)

            if stat_formula == 2:
                return 0
            
            return current_stat * current_coef
        
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.__get_string(formula_part_style_key)

        current_stat = current_block.get('mStat', 0)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')

        if stat_formula:
            icon_modifier = self.__get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

        value = getf(current_block, 'mCoefficient', 1.0)

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
    
    def __StatBySubPartCalculationPart(self, current_block, key=0):
        if self.needs_calculation:
            current_stat = self.champion_stats[current_block.get('mStat', 0)]
            current_value = self.__check_dict(self.parse_values(current_block['mSubpart']))

            stat_formula = current_block.get('mStatFormula', 1)

            if stat_formula == 2:
                return 0

            return current_stat * current_value
        
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.__get_string(formula_part_style_key)

        current_stat = current_block.get('mStat', 0)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')

        if stat_formula:
            icon_modifier = self.__get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

        value = self.__check_dict(self.parse_values(current_block['mSubpart'], key))

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
    
    def __AbilityResourceByCoefficientCalculationPart(self, current_block, key=0):
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.__get_string(formula_part_style_key)

        icon_modifier = ''
        stat_formula = current_block.get('mStatFormula')
        if stat_formula:
            icon_modifier = self.__get_string(f'tooltip_statsuidata_{stat_types[stat_formula]}iconmodifier')

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
    
    def __ByCharLevelBreakpointsCalculationPart(self, current_block, key=0):
        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.__get_string(formula_part_style_key)

        level1_value = current_block.get('mLevel1Value', 0)
        range_end = level1_value

        if 'mBreakpoints' in current_block:
            last_level = 18
            end_value = level1_value

            for m_breakpoint in reversed(current_block['mBreakpoints']):
                m_level = getf(m_breakpoint, 'mLevel', 0)

                if m_level > last_level:
                    continue

                if getf(m_breakpoint, 'mBonusPerLevelAtAndAfter'):
                    current_value = getf(m_breakpoint, 'mBonusPerLevelAtAndAfter')
                    diff = last_level - m_level + 1
                    end_value += diff * current_value
                    last_level -= diff
                elif getf(m_breakpoint, 'mAdditionalBonusAtThisLevel'):
                    current_value = getf(m_breakpoint, 'mAdditionalBonusAtThisLevel')
                    end_value += current_value

            range_end = round_number(end_value, 5)

        if getf(current_block, 'mInitialBonusPerLevel') and level1_value == range_end:
            range_end = round_number(getf(current_block, 'mInitialBonusPerLevel') * 17 + level1_value, 5)
        
        if level1_value == range_end:
            return round_number(float(level1_value), 5)

        placeholders = {
            '@OpeningTag@': '<scaleLevel>',
            '@RangeStart@': round_number(float(level1_value), 5),
            '@Icon@': '%i:scaleLevel%',
            '@RangeEnd@': round_number(float(range_end), 5),
            '@ClosingTag@': '</scaleLevel>'
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def __ByCharLevelFormulaCalculationPart(self, current_block, key=0):
        m_values = getf(current_block, 'mValues', [0] * 18)
        start_value = m_values[1]
        end_value = m_values[18]

        if not start_value:
            start_value = 0

        if not end_value:
            end_value = m_values[len(m_values) - 1]

        formula_part_style_key = "tooltip_statsuidata_formulapartrangestyle" if key == 0 else "tooltip_statsuidata_formulapartrangestylebonus"
        return_value = self.__get_string(formula_part_style_key)

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
    
    def __ProductOfSubPartsCalculationPart(self, current_block, key=0):
        m_part1 = self.__check_dict(self.parse_values(current_block['mPart1']))
        m_part2 = self.__check_dict(self.parse_values(current_block['mPart2']))

        if m_part2 == '1':
            return m_part1

        try:
            m_part1 = float(m_part1)
            m_part2 = float(m_part2)
        except:
            pass

        if isinstance(m_part1, (int, float)) and isinstance(m_part2, (int, float)):
            return round_number(m_part1 * m_part2, 5)
        else:
            return self.__ProductOfSubPartsCalculationPart_str(current_block)
        
    def __ProductOfSubPartsCalculationPart_str(self, current_block):
        m_part1 = self.__check_dict(self.parse_values(current_block['mPart1']))
        m_part2 = self.__check_dict(self.parse_values(current_block['mPart2']))

        try:
            m_part1 = round_number(float(m_part1), 5)
        except:
            pass

        try:
            m_part2 = round_number(float(m_part2), 5)
        except:
            pass

        return f'({str(m_part1)} * {str(m_part2)})'
    
    def __SumOfSubPartsCalculationPart(self, current_block, key=0):
        if len(current_block['mSubparts']) == 1:
            return self.__check_dict(self.parse_values(current_block['mSubparts'][0]))
        
        total_sum = 0
        for subpart in current_block['mSubparts']:
            parsed_value = self.__check_dict(self.parse_values(subpart))

            try:
                parsed_value = float(parsed_value)
            except:
                pass

            if isinstance(parsed_value, (int, float)):
                total_sum += parsed_value
            else:
                return self.__SumOfSubPartsCalculationPart_str(current_block)
        
        return total_sum
    
    def __SumOfSubPartsCalculationPart_str(self, current_block):
        total_sum = ''

        for subpart in current_block['mSubparts']:
            formula_part_style_key = "tooltip_statsuidata_formulapartstyle" if total_sum == '' else "tooltip_statsuidata_formulapartstylebonus"
            return_value = self.__get_string(formula_part_style_key)

            parsed_value = self.__check_dict(self.parse_values(subpart))

            placeholders = {
                '@OpeningTag@': '',
                '@IconModifier@': '',
                '@Icon@': '',
                '@ClosingTag@': '',
                '@Value@': str(parsed_value)
            }

            for placeholder, replacement in placeholders.items():
                return_value = str_ireplace(placeholder, replacement, return_value)
                
            total_sum += return_value if total_sum == '' else ' ' + return_value
        
        return f'({total_sum})'

    def __GameCalculationModified(self, current_block, key=0):
        multiplier = self.__check_dict(self.parse_values(current_block['mMultiplier']))
        modified_block = self.__check_dict(self.parse_values(self.all_calculations[current_block['mModifiedGameCalculation']]))

        if not multiplier:
            multiplier = 1

        try:
            multiplier = float(multiplier)
        except:
            matches = re.match(r"^([0-9\.]+)", multiplier)
            multiplier = float(matches.group(1)) if matches else 1

        def callback_for_numbers(matches):
            number = float(matches.group(1))
            result = number * multiplier
            return round_number(result, 5, True)

        return re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, str(modified_block), flags=re.IGNORECASE)
    
    def __f3cbe7b2(self, current_block, key=0):
        return self.__check_dict(self.parse_values(self.all_calculations[getf(current_block, 'mSpellCalculationKey')]))
    
    def __ClampSubPartsCalculationPart(self, current_block, key=0):
        if self.needs_calculation:
            floor = current_block.get('mFloor')
            ceiling = current_block.get('mCeiling')
            subparts = current_block.get('mSubparts')

            if subparts and len(subparts) > 0:
                calculated_subparts = self.__check_dict(self.parse_values(subparts[0]))

                if floor and calculated_subparts < floor:
                    return floor
                
                if ceiling and calculated_subparts > ceiling:
                    return ceiling
                
                return calculated_subparts
            
            return 0
        
        return 0
    
    def __StatEfficiencyPerHundred(self, current_block, key=0):
        if self.needs_calculation:
            current_value = self.var_values.get(current_block['mDataValue'].lower(), 0)
            current_coef = getf(current_block, 'mBonusStatForEfficiency') # doesn't work well with mDisplayAsPercent
            
            return current_value # * current_coef

        return 0
    
    def __e9a3c91d(self, current_block, key=0):
        return_value = self.__get_string("item_range_type_melee")

        ranged_coef = self.parse_values(getf(current_block, 'mRangedMultiplier'))
        current_block_ranged = dict(current_block)
        current_block_ranged['mMultiplier'] = ranged_coef

        melee_value = self.__GameCalculation(current_block)
        ranged_value = self.__GameCalculation(current_block_ranged)

        placeholders = {
            '@MeleeItemCalcValue@': melee_value,
            '@RangedItemCalcValue@': ranged_value
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def __4750ceb6(self, current_block, key=0):
        return_value = self.__get_string("item_range_type_melee")

        melee_value = 0
        ranged_value = 0

        if getf(current_block, 'MeleeResult'):
            block_name = getf(current_block, 'MeleeResult').replace('@', '')
            temp_block = getf(self.all_calculations, block_name)

            if self.var_values.get(block_name.lower()):
                melee_value = round_number(self.var_values[block_name.lower()], 5, True)

            if temp_block:
                melee_value = self.parse_values(temp_block)

        if getf(current_block, 'RangedResult'):
            block_name = getf(current_block, 'RangedResult').replace('@', '')
            temp_block = getf(self.all_calculations, block_name)

            if self.var_values.get(block_name.lower()):
                ranged_value = round_number(self.var_values[block_name.lower()], 5, True)

            if temp_block:
                ranged_value = self.parse_values(temp_block)

        placeholders = {
            '@MeleeItemCalcValue@': melee_value,
            '@RangedItemCalcValue@': ranged_value
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def __SubPartScaledProportionalToStat(self, current_block, key=0):
        if self.needs_calculation:
            current_stat = self.champion_stats[current_block.get('mStat', 0)]
            current_ratio = current_block.get('mRatio', 1)
            current_value = self.__check_dict(self.parse_values(current_block['mSubpart']))

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
        
        formula_part_style_key = "tooltip_statsuidata_formulapartstylepercent" if key == 0 else "tooltip_statsuidata_formulapartstylebonuspercent"
        return_value = self.__get_string(formula_part_style_key)
        
        current_subpart = self.__check_dict(self.parse_values(current_block['mSubpart']))
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