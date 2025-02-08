from ..bin_calc import *
from .GameCalculation import GameCalculation

class h_e9a3c91d(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return_value = self.get_string("item_range_type_melee")

        ranged_coef = self.calc_values(getf(current_block, 'mRangedMultiplier'))
        current_block_ranged = dict(current_block)
        current_block_ranged['mMultiplier'] = ranged_coef

        game_calculation = GameCalculation(self.strings_raw, self.var_values, self.all_calculations, self.champion_stats)
        melee_value = game_calculation.calc_string(current_block, key)
        ranged_value = game_calculation.calc_string(current_block_ranged, key)

        placeholders = {
            '@MeleeItemCalcValue@': str(melee_value),
            '@RangedItemCalcValue@': str(ranged_value)
        }

        for placeholder, replacement in placeholders.items():
            return_value = re.sub(placeholder, replacement, return_value, flags=re.IGNORECASE)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0