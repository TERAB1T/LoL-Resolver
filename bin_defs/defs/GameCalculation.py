from ..bin_calc import *

class GameCalculation(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        m_formula_parts = []
        calculated_tag = None
        calculated_icon = None

        for i, value in enumerate(current_block['mFormulaParts']):
            current_value = self.calc_values(value, i)

            if re.match(r'^-?\d*\.?\d*$', str(current_value)):
                current_value = float(current_value)

            m_formula_parts.append(round_number(current_value, 5))

        if all(isinstance(x, (int, float)) for x in m_formula_parts):
            return_value = sum(m_formula_parts)
        else:
            return_value = ' '.join(str(x) for x in m_formula_parts)

        if 'mMultiplier' in current_block:
            def callback_for_multiplier(matches):
                number = float(matches.group(1))
                return round_number(number * mMultiplier, 5, True)
            
            mMultiplier = self.calc_values(current_block['mMultiplier'])

            if not mMultiplier:
                mMultiplier = 1

            try:
                mMultiplier = float(mMultiplier)
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_multiplier, str(return_value))
            except:
                pass

        #return_value = f'({return_value})'

        if 'mDisplayAsPercent' in current_block:
            if is_number(return_value):
                return_value = re.sub('@NUMBER@', round_number(float(return_value) * 100, getf(current_block, 'mPrecision', 5), True), self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE)
            elif '%i:scaleLevel%' in return_value:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return round_number(number * 100, 5, True)
                
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)
                return_value = re.sub('@NUMBER@', return_value.split('%i:scaleLevel%')[0], self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE) + '%i:scaleLevel%' + return_value.split('%i:scaleLevel%')[1]
            else:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return round_number(number * 100, 5, True)

                return_value = re.sub(r'^([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)
                #return_value = f'({return_value})'
                return_value = re.sub('@NUMBER@', return_value, self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE)
                
                #return_value = f'({return_value} * 100)%'

        if calculated_tag and calculated_icon:
            return {
                'value': return_value,
                'tag': calculated_tag,
                'icon': calculated_icon
            }
        else:
            return return_value
    
    def calc_float(self, current_block, key):
        m_formula_parts = []
        calculated_tag = None
        calculated_icon = None

        for i, value in enumerate(current_block['mFormulaParts']):
            block_calculation = self.calc_values(value, i, 'float')

            if isinstance(block_calculation, dict):
                calculated_value = block_calculation['value']
                calculated_tag = block_calculation['tag']
                calculated_icon = block_calculation['icon']
            else:
                calculated_value = block_calculation

            m_formula_parts.append(float(round_number(calculated_value, 5, True)))

        return_value = sum(m_formula_parts)

        if 'mMultiplier' in current_block:
            def callback_for_multiplier(matches):
                number = float(matches.group(1))
                return round_number(number * mMultiplier, 5, True)
            
            mMultiplier = self.calc_values(current_block['mMultiplier'], 0, 'float')

            if not mMultiplier:
                mMultiplier = 1

            try:
                mMultiplier = float(mMultiplier)
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_multiplier, str(return_value))
            except:
                pass

        if 'mDisplayAsPercent' in current_block:
            if isinstance(return_value, (int, float)):
                return_value = re.sub('@NUMBER@', round_number(return_value * 100, getf(current_block, 'mPrecision', 5), True), self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE)
            elif '%i:scaleLevel%' in return_value:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return round_number(number * 100, 5, True)
                
                return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)
                return_value = re.sub('@NUMBER@', return_value.split('%i:scaleLevel%')[0], self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE) + '%i:scaleLevel%' + return_value.split('%i:scaleLevel%')[1]
            else:
                def callback_for_numbers(matches):
                    number = float(matches.group(1))
                    return re.sub('@NUMBER@', round_number(number * 100, 5, True), self.get_string('number_formatting_percentage_format'), flags=re.IGNORECASE)

                return_value = re.sub(r'^([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)
                #return_value = f'({return_value} * 100)%'

        if calculated_tag and calculated_icon:
            return {
                'value': return_value,
                'tag': calculated_tag,
                'icon': calculated_icon
            }
        else:
            return return_value