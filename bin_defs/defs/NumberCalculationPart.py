from ..bin_calc import *

class NumberCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return getf(current_block, 'mNumber', 0)
    
    def calc_float(self, current_block, key):
        return getf(current_block, 'mNumber', 0)