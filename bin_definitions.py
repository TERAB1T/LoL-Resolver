from utils import *
from stats import *

class BinDefinitions:
    def __init__(self, strings, var_values, all_calculations):
        self.strings_raw = strings
        self.var_values = var_values
        self.all_calculations = all_calculations

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def parse_values(self, current_block, key=0):
        if not isinstance(current_block, (list, dict)):
            return current_block
        
        block_type = current_block['__type']

        if block_type in [
            'GameCalculation',
            'ByCharLevelInterpolationCalculationPart',
            'NamedDataValueCalculationPart',
            'NumberCalculationPart',
            'EffectValueCalculationPart',
            'StatByNamedDataValueCalculationPart',
            'StatByCoefficientCalculationPart',
            'StatBySubPartCalculationPart',
            'AbilityResourceByCoefficientCalculationPart',
            'ByCharLevelBreakpointsCalculationPart',
            'ProductOfSubPartsCalculationPart',
            'SumOfSubPartsCalculationPart',
            'GameCalculationModified',
            '{f3cbe7b2}'
        ]:
            return getattr(self, f'_BinDefinitions__{block_type.strip("{}")}')(current_block, key)
        elif block_type in ['BuffCounterByCoefficientCalculationPart', 'BuffCounterByNamedDataValueCalculationPart', '{803dae4c}', '{663d5e00}']:
            return 0
        else:
            return current_block
    
    def __GameCalculation(self, current_block, key=0):
        mFormulaParts = {}

        for i, value in enumerate(current_block['mFormulaParts']):
            mFormulaParts[i] = str(round_number(self.parse_values(value, i), 5, True))

        return_value = ' '.join(mFormulaParts.values())

        if 'mMultiplier' in current_block:
            mMultiplier = self.parse_values(current_block['mMultiplier'])

            try:
                mMultiplier = float(mMultiplier)
                return_value = float(return_value)
            except:
                pass

            if isinstance(return_value, (int, float)):
                return_value = round_number(return_value * mMultiplier, 5)

        if 'mDisplayAsPercent' in current_block:
            if isinstance(return_value, (int, float)):
                return_value = str_ireplace('@NUMBER@', round_number(return_value * 100, not_none(current_block.get('mPrecision'), 5)), self.__get_string('number_formatting_percentage_format'))
            else:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return str_ireplace('@NUMBER@', round_number(number * 100, 5, True), self.__get_string('number_formatting_percentage_format'))

                return_value = re.sub(r'^([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)

        return return_value
    
    def __ByCharLevelInterpolationCalculationPart(self, current_block, key=0):
        return_value = ""

        if 'mStartValue' not in current_block:
            return_value = not_none(current_block.get('mEndValue'), '0')
        else:
            if key == 0:
                return_value = self.__get_string("tooltip_statsuidata_formulapartrangestyle")
            else:
                return_value = self.__get_string("tooltip_statsuidata_formulapartrangestylebonus")

            return_value = str_ireplace('@OpeningTag@', '<scaleLevel>', return_value)
            return_value = str_ireplace('@RangeStart@', round_number(float(current_block['mStartValue']), 5), return_value)
            return_value = str_ireplace('@RangeEnd@', round_number(float(current_block['mEndValue']), 5), return_value)
            return_value = str_ireplace('@Icon@', '%i:scaleLevel%', return_value)
            return_value = str_ireplace('@ClosingTag@', '</scaleLevel>', return_value)

        return return_value
    
    def __NamedDataValueCalculationPart(self, current_block, key=0):
        return_value = 0

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstyle")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonus")

        return_value = str_ireplace('@OpeningTag@', "", return_value)
        return_value = str_ireplace('@IconModifier@', '', return_value)
        return_value = str_ireplace('@Icon@', "", return_value)
        return_value = str_ireplace('@ClosingTag@', "", return_value)

        data_value = current_block['mDataValue'].lower()
        if data_value in self.var_values:
            return_value = str_ireplace('@Value@', round_number(self.var_values[data_value], 5), return_value)
        else:
            return_value = str_ireplace('@Value@', 0, return_value)

        return return_value
    
    def __NumberCalculationPart(self, current_block, key=0):
        return current_block['mNumber']
    
    def __EffectValueCalculationPart(self, current_block, key=0):
        return self.var_values['effect' + str(current_block['mEffectIndex']) + 'amount']
    
    def __StatByNamedDataValueCalculationPart(self, current_block, key=0):
        return_value = ""
        current_stat = not_none(current_block.get('mStat'), 0)

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

        if 'mStatFormula' in current_block:
            return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
        else:
            return_value = str_ireplace('@IconModifier@', '', return_value)

        return_value = str_ireplace('@OpeningTag@', stats[current_stat]['openingTag'], return_value)

        value = self.var_values[current_block['mDataValue'].lower()]
        try:
            value = float(value) * 100
        except:
            pass
        return_value = str_ireplace('@Value@', round_number(value, 5), return_value)

        return_value = str_ireplace('@Icon@', stats[current_stat]['icon'], return_value)
        return_value = str_ireplace('@ClosingTag@', stats[current_stat]['closingTag'], return_value)

        return return_value
    
    def __StatByCoefficientCalculationPart(self, current_block, key=0):
        return_value = ""
        current_stat = not_none(current_block.get('mStat'), 0)

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

        if 'mStatFormula' in current_block:
            return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
        else:
            return_value = str_ireplace('@IconModifier@', '', return_value)

        return_value = str_ireplace('@OpeningTag@', stats[current_stat]['openingTag'], return_value)

        value = current_block['mCoefficient']
        try:
            value = float(value) * 100
        except:
            pass
        return_value = str_ireplace('@Value@', round_number(value, 5), return_value)

        return_value = str_ireplace('@Icon@', stats[current_stat]['icon'], return_value)
        return_value = str_ireplace('@ClosingTag@', stats[current_stat]['closingTag'], return_value)

        return return_value
    
    def __StatBySubPartCalculationPart(self, current_block, key=0):
        return_value = ""
        current_stat = not_none(current_block.get('mStat'), 0)

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

        if 'mStatFormula' in current_block:
            return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
        else:
            return_value = str_ireplace('@IconModifier@', '', return_value)

        return_value = str_ireplace('@OpeningTag@', stats[current_stat]['openingTag'], return_value)

        value = self.parse_values(current_block['mSubpart'], key)
        try:
            value = float(value) * 100
        except:
            pass
        return_value = str_ireplace('@Value@', round_number(value, 5), return_value)

        return_value = str_ireplace('@Icon@', stats[current_stat]['icon'], return_value)
        return_value = str_ireplace('@ClosingTag@', stats[current_stat]['closingTag'], return_value)

        return return_value
    
    def __AbilityResourceByCoefficientCalculationPart(self, current_block, key=0):
        return_value = ""

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

        if 'mStatFormula' in current_block:
            return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
        else:
            return_value = str_ireplace('@IconModifier@', '', return_value)

        return_value = str_ireplace('@OpeningTag@', '<scalemana>', return_value)

        value = current_block['mCoefficient']
        try:
            value = float(value) * 100
        except:
            pass

        return_value = str_ireplace('@Value@', round_number(value, 5), return_value)
        return_value = str_ireplace('@Icon@', '%i:scaleMana%', return_value)
        return_value = str_ireplace('@ClosingTag@', '</scalemana>', return_value)

        return return_value
    
    def __ByCharLevelBreakpointsCalculationPart(self, current_block, key=0):
        return_value = ""

        if key == 0:
            return_value = self.__get_string("tooltip_statsuidata_formulapartrangestyle")
        else:
            return_value = self.__get_string("tooltip_statsuidata_formulapartrangestylebonus")

        if 'mLevel1Value' not in current_block:
            current_block['mLevel1Value'] = 0

        return_value = str_ireplace('@OpeningTag@', '<scaleLevel>', return_value)
        return_value = str_ireplace('@RangeStart@', round_number(float(current_block['mLevel1Value']), 5), return_value)
        return_value = str_ireplace('@Icon@', '%i:scaleLevel%', return_value)
        return_value = str_ireplace('@ClosingTag@', '</scaleLevel>', return_value)

        if 'mBreakpoints' in current_block:
            last_level = 18
            end_value = current_block['mLevel1Value']

            for m_breakpoint in reversed(current_block['mBreakpoints']):
                current_value = not_none(m_breakpoint.get('{d5fd07ed}'), not_none(m_breakpoint.get('{57fdc438}'), 0))
                diff = last_level - m_breakpoint['mLevel'] + 1
                end_value += diff * current_value
                last_level -= diff

            return_value = str_ireplace('@RangeEnd@', round_number(end_value, 5), return_value)
        else:
            return_value = str_ireplace('@RangeEnd@', round_number(current_block['{02deb550}'] * 17 + current_block['mLevel1Value'], 5), return_value)

        return return_value
    
    def __ProductOfSubPartsCalculationPart(self, current_block, key=0):
        return_value = ""

        m_part1 = self.parse_values(current_block['mPart1'])
        m_part2 = self.parse_values(current_block['mPart2'])

        try:
            m_part1 = float(m_part1)
            m_part2 = float(m_part2)
        except:
            pass

        if isinstance(m_part1, (int, float)) and isinstance(m_part2, (int, float)):
            return_value = round_number(m_part1 * m_part2, 5)
        else:
            return_value = 0

        return return_value
    
    def __SumOfSubPartsCalculationPart(self, current_block, key=0):
        return_value = ""

        if len(current_block['mSubparts']) == 1:
            return_value = self.parse_values(current_block['mSubparts'][0])
        else:
            summ = 0

            for value in current_block['mSubparts']:
                current_value = self.parse_values(value)

                if not isinstance(current_value, (int, float)):
                    summ = 0
                    break
                else:
                    summ += current_value

            return_value = summ

        return return_value
    
    def __GameCalculationModified(self, current_block, key=0):
        return_value = ""

        multiplier = self.parse_values(current_block['mMultiplier'])
        modified_block = self.parse_values(self.all_calculations[current_block['mModifiedGameCalculation']])

        try:
            multiplier = float(multiplier)
        except:
            matches = re.match(r"^([0-9\.]+)", multiplier)
            if matches:
                multiplier = float(matches.group(1))
            else:
                multiplier = 1

        def callback_for_numbers(matches):
            number = float(matches.group(1))
            result = number * multiplier
            return round_number(result, 5, True)

        return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, str(modified_block), flags=re.IGNORECASE)

        return return_value
    
    def __f3cbe7b2(self, current_block, key=0):
        return self.parse_values(self.all_calculations[current_block['{88536426}']])