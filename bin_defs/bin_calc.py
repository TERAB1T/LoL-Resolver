from utils import *
from stats import *
from .bin_main import BinDefinitions

class BinCalculation:
    def __init__(self, strings, var_values, all_calculations, champion_stats):
        self.strings_raw = strings
        self.var_values = var_values
        self.all_calculations = all_calculations
        self.champion_stats = champion_stats

    def get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def check_dict(self, value):
        if isinstance(value, dict) and 'icon' in value:
            value = value['value']
        
        return value
    
    def calc_values(self, current_block, key=0, calc_type = 'string'):
        bin_definitions = BinDefinitions(self.strings_raw, self.var_values, self.all_calculations, self.champion_stats, calc_type)
        return bin_definitions.calc_values(current_block, key)