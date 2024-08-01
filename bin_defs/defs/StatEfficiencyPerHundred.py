from ..bin_calc import *

class StatEfficiencyPerHundred(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return '@CalcError@'
    
    def calc_float(self, current_block, key):
        current_value = self.var_values.get(current_block['mDataValue'].lower(), 0)
        current_coef = getf(current_block, 'mBonusStatForEfficiency') # doesn't work well with mDisplayAsPercent
            
        return current_value # * current_coef