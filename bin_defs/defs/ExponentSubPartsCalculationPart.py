from ..bin_calc import *

class ExponentSubPartsCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return '@CalcError@'
    
    def calc_float(self, current_block, key):
        part1 = self.calc_values(getf(current_block, 'part1'), 0, 'float')
        part2 = self.calc_values(getf(current_block, 'part2'), 0, 'float')
            
        return part1 ** part2