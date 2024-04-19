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
            'ByCharLevelInterpolationCalculationPart',
            'NamedDataValueCalculationPart',
            'NumberCalculationPart',
            'EffectValueCalculationPart',
            'AbilityResourceByCoefficientCalculationPart',
            'ByCharLevelBreakpointsCalculationPart',
            'ProductOfSubPartsCalculationPart',
            'SumOfSubPartsCalculationPart',
            'GameCalculationModified',
            'StatByNamedDataValueCalculationPart',
            'StatByCoefficientCalculationPart',
            'StatBySubPartCalculationPart',
            '{f3cbe7b2}',
            '{803dae4c}',
            '{05abdfab}',
            '{e9a3c91d}',
            '{4750ceb6}',
            'SubPartScaledProportionalToStat'
            ]

        if block_type in known_types:
            return getattr(self, f'_BinDefinitions__{block_type.strip("{}")}')(current_block, key)
        elif block_type in [
            'BuffCounterByCoefficientCalculationPart',
            'BuffCounterByNamedDataValueCalculationPart',
            '{663d5e00}'
            ]:
            return 0
        else:
            for current_type in known_types:
                if block_type == hash_fnv1a(current_type):
                    return getattr(self, f'_BinDefinitions__{current_type.strip("{}")}')(current_block, key)

            return '@CalcError@' #current_block
    
    def __GameCalculation(self, current_block, key=0):
        mFormulaParts = {}
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

                mFormulaParts[i] = float(round_number(calculated_value, 5, True))
            else:
                mFormulaParts[i] = str(round_number(self.parse_values(value, i), 5, True))

        if self.needs_calculation:
            return_value = sum(mFormulaParts.values())
        else:
            return_value = ' '.join(mFormulaParts.values())

        if 'mMultiplier' in current_block:
            def callback_for_multiplier(matches):
                number = float(matches.group(1))
                return round_number(number * mMultiplier, 5, True)
            
            mMultiplier = self.parse_values(current_block['mMultiplier'])

            try:
                mMultiplier = float(mMultiplier)
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_multiplier, str(return_value))
            except:
                pass

        if 'mDisplayAsPercent' in current_block:
            if isinstance(return_value, (int, float)):
                return_value = str_ireplace('@NUMBER@', round_number(return_value * 100, not_none(current_block.get('mPrecision'), 5)), self.__get_string('number_formatting_percentage_format'))
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
    
    def __ByCharLevelInterpolationCalculationPart(self, current_block, key=0):
        if 'mStartValue' not in current_block:
            return not_none(current_block.get('mEndValue'), '0')

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
        return current_block['mNumber']
    
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

        value = current_block['mCoefficient']

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

        if 'mBreakpoints' in current_block:
            last_level = 18
            end_value = level1_value

            for m_breakpoint in reversed(current_block['mBreakpoints']):
                current_value = not_none(m_breakpoint.get('{d5fd07ed}'), not_none(m_breakpoint.get('{57fdc438}'), 0))
                diff = last_level - m_breakpoint['mLevel'] + 1
                end_value += diff * current_value
                last_level -= diff

            range_end = round_number(end_value, 5)
        else:
            range_end = round_number(current_block['{02deb550}'] * 17 + level1_value, 5)

        placeholders = {
            '@OpeningTag@': '<scaleLevel>',
            '@RangeStart@': round_number(float(level1_value), 5),
            '@Icon@': '%i:scaleLevel%',
            '@RangeEnd@': range_end,
            '@ClosingTag@': '</scaleLevel>'
        }

        for placeholder, replacement in placeholders.items():
            return_value = str_ireplace(placeholder, replacement, return_value)

        return return_value
    
    def __ProductOfSubPartsCalculationPart(self, current_block, key=0):
        m_part1 = self.__check_dict(self.parse_values(current_block['mPart1']))
        m_part2 = self.__check_dict(self.parse_values(current_block['mPart2']))

        try:
            m_part1 = float(m_part1)
            m_part2 = float(m_part2)
        except:
            pass

        if isinstance(m_part1, (int, float)) and isinstance(m_part2, (int, float)):
            return round_number(m_part1 * m_part2, 5)
        else:
            return 0
    
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
                return 0
        
        return total_sum

    def __GameCalculationModified(self, current_block, key=0):
        multiplier = self.__check_dict(self.parse_values(current_block['mMultiplier']))
        modified_block = self.__check_dict(self.parse_values(self.all_calculations[current_block['mModifiedGameCalculation']]))

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
        return self.__check_dict(self.parse_values(self.all_calculations[current_block['{88536426}']]))
    
    def __803dae4c(self, current_block, key=0):
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
    
    def __05abdfab(self, current_block, key=0):
        if self.needs_calculation:
            current_value = self.var_values.get(current_block['mDataValue'].lower(), 0)
            current_coef = current_block['{bfe6ad01}'] # doesn't work well with mDisplayAsPercent
            
            return current_value # * current_coef

        return 0
    
    def __e9a3c91d(self, current_block, key=0):
        return_value = self.__get_string("item_range_type_melee")

        ranged_coef = self.parse_values(current_block['{68508370}'])
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

        if "{f61974d2}" in current_block:
            block_name = current_block["{f61974d2}"].replace('@', '')
            temp_block = getf(self.all_calculations, block_name)

            if self.var_values.get(block_name.lower()):
                melee_value = round_number(self.var_values[block_name.lower()], 5, True)

            if temp_block:
                melee_value = self.parse_values(temp_block)

        if "{158508fb}" in current_block:
            block_name = current_block["{158508fb}"].replace('@', '')
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

            current_tag = current_block.get('mStyleTag', current_block.get('{992cd7eb}'))
            current_icon = current_block.get('{a5749b52}')

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