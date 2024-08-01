from ..bin_calc import *

class ByItemEpicnessCountCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return '@CalcError@'
    
    def calc_float(self, current_block, key):
        return 0