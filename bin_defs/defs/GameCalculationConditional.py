from ..bin_calc import *

class GameCalculationConditional(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        default_game_calculation = getf(current_block, 'mDefaultGameCalculation')
        return self.calc_values(self.all_calculations[default_game_calculation], key)
    
    def calc_float(self, current_block, key):
        default_game_calculation = getf(current_block, 'mDefaultGameCalculation')
        return self.calc_values(self.all_calculations[default_game_calculation], key, 'float')