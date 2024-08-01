import importlib
from utils import *

class BinDefinitions:
    known_defs = [
        'GameCalculation',
        'GameCalculationConditional',
        'GameCalculationModified',

        'AbilityResourceByCoefficientCalculationPart',
        'BuffCounterByCoefficientCalculationPart',
        'BuffCounterByNamedDataValueCalculationPart',
        'ByCharLevelBreakpointsCalculationPart',
        'ByCharLevelFormulaCalculationPart',
        'ByCharLevelInterpolationCalculationPart',
        'ByItemEpicnessCountCalculationPart',
        'ClampSubPartsCalculationPart',
        'CooldownMultiplierCalculationPart',
        'EffectValueCalculationPart',
        'ExponentSubPartsCalculationPart',
        'NamedDataValueCalculationPart',
        'NumberCalculationPart',
        'ProductOfSubPartsCalculationPart',
        'StatByCoefficientCalculationPart',
        'StatByNamedDataValueCalculationPart',
        'StatBySubPartCalculationPart',
        'StatEfficiencyPerHundred',
        'SubPartScaledProportionalToStat',
        'SumOfSubPartsCalculationPart',

        '{4750ceb6}',
        '{e9a3c91d}',
        '{f3cbe7b2}'
    ]

    def __init__(self, strings, var_values, all_calculations, champion_stats = {}, calc_type = 'string'):
        self.strings_raw = strings
        self.var_values = var_values
        self.all_calculations = all_calculations
        self.champion_stats = champion_stats
        self.calc_type = calc_type

        self.defs = {}
        self.populate_types()

    def get_calc_def(self, current_def):
        try:
            current_def = self.defs[current_def]
            module_name = f'bin_defs.defs.{current_def}'
            module = importlib.import_module(module_name)
            return getattr(module, current_def)
        except:
            return None
    
    def populate_types(self):
        for current_def in self.known_defs:
            if is_fnv1a(current_def):
                self.defs[current_def] = 'h_' + current_def.strip("{}")
            else:
                self.defs[current_def] = current_def
                self.defs[hash_fnv1a(current_def)] = current_def

    def calc_values(self, current_block, key=0):
        if not isinstance(current_block, (list, dict)):
            return current_block
        
        current_def = getf(current_block, '__type', '')

        def_class_name = self.get_calc_def(current_def)

        if def_class_name:
            def_class = def_class_name(self.strings_raw, self.var_values, self.all_calculations, self.champion_stats)

            if self.calc_type == 'string':
                return def_class.calc_string(current_block, key)
            elif self.calc_type == 'float':
                return def_class.calc_float(current_block, key)
        
        return '@CalcError@'