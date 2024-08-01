from ..bin_calc import *

class EffectValueCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        effect_key = f"effect{current_block['mEffectIndex']}amount"
        return self.var_values.get(effect_key, 0)
    
    def calc_float(self, current_block, key):
        return 0