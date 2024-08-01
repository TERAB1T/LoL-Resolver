from ..bin_calc import *

class GameCalculationModified(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        multiplier = self.check_dict(self.calc_values(current_block['mMultiplier']))
        modified_block = self.check_dict(self.calc_values(self.all_calculations[current_block['mModifiedGameCalculation']]))

        if not multiplier:
            multiplier = 1

        try:
            multiplier = float(multiplier)
        except:
            matches = re.match(r"^([0-9\.]+)", multiplier)
            multiplier = float(matches.group(1)) if matches else 1

        def callback_for_numbers(matches):
            number = float(matches.group(1))
            result = number * multiplier
            return round_number(result, 5, True)

        return re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, str(modified_block), flags=re.IGNORECASE)
    
    def calc_float(self, current_block, key):
        multiplier = self.check_dict(self.calc_values(current_block['mMultiplier'], 0, 'float'))
        modified_block = self.check_dict(self.calc_values(self.all_calculations[current_block['mModifiedGameCalculation']], 0, 'float'))

        if not multiplier:
            multiplier = 1

        try:
            multiplier = float(multiplier)
        except:
            matches = re.match(r"^([0-9\.]+)", multiplier)
            multiplier = float(matches.group(1)) if matches else 1

        def callback_for_numbers(matches):
            number = float(matches.group(1))
            result = number * multiplier
            return round_number(result, 5, True)

        return re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, str(modified_block), flags=re.IGNORECASE)