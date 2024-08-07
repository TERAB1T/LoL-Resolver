from ..bin_calc import *

class ProductOfSubPartsCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        m_part1 = self.calc_values(current_block['mPart1'])
        m_part2 = self.calc_values(current_block['mPart2'])

        if m_part1 == '1':
            return m_part2
        
        if m_part2 == '1':
            return m_part1

        try:
            m_part1 = float(m_part1)
        except:
            pass

        try:
            m_part2 = float(m_part2)
        except:
            pass

        if '%i:scaleLevel%' in str(m_part1) and isinstance(m_part2, float):
            return self.__multiply_range(m_part1, m_part2)
        
        if '%i:scaleLevel%' in str(m_part2) and isinstance(m_part1, float):
            return self.__multiply_range(m_part2, m_part1)

        if isinstance(m_part1, (int, float)) and isinstance(m_part2, (int, float)):
            return round_number(m_part1 * m_part2, 5)
        else:
            return self.__ProductOfSubPartsCalculationPart_str(current_block)
    
    def calc_float(self, current_block, key):
        m_part1 = self.check_dict(self.calc_values(current_block['mPart1'], 0, 'float'))
        m_part2 = self.check_dict(self.calc_values(current_block['mPart2'], 0, 'float'))

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
        
    def __multiply_range(self, range, multiplier):
        def callback_for_numbers(matches):
            number = float(matches.group(1))
            return round_number(number * multiplier, 5, True)
        
        return re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, range)
    
    def __ProductOfSubPartsCalculationPart_str(self, current_block):
        m_part1 = self.check_dict(self.calc_values(current_block['mPart1']))
        m_part2 = self.check_dict(self.calc_values(current_block['mPart2']))

        try:
            m_part1 = round_number(float(m_part1), 5)
        except:
            pass

        try:
            m_part2 = round_number(float(m_part2), 5)
        except:
            pass

        return f'({str(m_part1)} * {str(m_part2)})'