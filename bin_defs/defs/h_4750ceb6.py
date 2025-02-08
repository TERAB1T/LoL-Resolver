from ..bin_calc import *

class h_4750ceb6(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        return_value = self.get_string("item_range_type_melee")

        melee_value = 0
        ranged_value = 0

        if getf(current_block, 'MeleeResult'):
            block_name = getf(current_block, 'MeleeResult').replace('@', '')
            temp_block = getf(self.all_calculations, block_name)

            if self.var_values.get(block_name.lower()):
                melee_value = round_number(self.var_values[block_name.lower()], 5, True)

            if temp_block:
                melee_value = self.calc_values(temp_block)

        if getf(current_block, 'RangedResult'):
            block_name = getf(current_block, 'RangedResult').replace('@', '')
            temp_block = getf(self.all_calculations, block_name)

            if self.var_values.get(block_name.lower()):
                ranged_value = round_number(self.var_values[block_name.lower()], 5, True)

            if temp_block:
                ranged_value = self.calc_values(temp_block)

        placeholders = {
            '@MeleeItemCalcValue@': str(melee_value),
            '@RangedItemCalcValue@': str(ranged_value)
        }

        for placeholder, replacement in placeholders.items():
            return_value = re.sub(placeholder, replacement, return_value, flags=re.IGNORECASE)

        return return_value
    
    def calc_float(self, current_block, key):
        return 0