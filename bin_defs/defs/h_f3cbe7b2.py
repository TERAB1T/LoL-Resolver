from ..bin_calc import *

class h_f3cbe7b2(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return self.check_dict(self.calc_values(self.all_calculations[getf(current_block, 'mSpellCalculationKey')]))
    
    def calc_float(self, current_block, key):
        return 0