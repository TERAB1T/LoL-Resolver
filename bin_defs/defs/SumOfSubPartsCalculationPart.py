from ..bin_calc import *

class SumOfSubPartsCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        if len(current_block['mSubparts']) == 1:
            return self.calc_values(current_block['mSubparts'][0])
        
        total_sum = 0
        for subpart in current_block['mSubparts']:
            parsed_value = self.calc_values(subpart)
            subpart_type = getf(subpart, '__type')

            if subpart_type == 'StatByCoefficientCalculationPart':
                continue

            try:
                parsed_value = float(parsed_value)
            except:
                pass

            if isinstance(parsed_value, (int, float)):
                total_sum += parsed_value
            else:
                return self.__SumOfSubPartsCalculationPart_str(current_block)
        
        return total_sum
    
    def calc_float(self, current_block, key):
        if len(current_block['mSubparts']) == 1:
            return self.check_dict(self.calc_values(current_block['mSubparts'][0], 0, 'float'))
        
        total_sum = 0
        for subpart in current_block['mSubparts']:
            parsed_value = self.check_dict(self.calc_values(subpart, 0, 'float'))

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
            return_value = self.get_string(formula_part_style_key)

            parsed_value = self.check_dict(self.calc_values(subpart))

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