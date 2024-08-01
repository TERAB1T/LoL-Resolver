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

        self.defs = {'GameCalculation': 'GameCalculation', '{bc409284}': 'GameCalculation', 'GameCalculationConditional': 'GameCalculationConditional', '{e9ced584}': 'GameCalculationConditional', 'GameCalculationModified': 'GameCalculationModified', '{070e3593}': 'GameCalculationModified', 'AbilityResourceByCoefficientCalculationPart': 'AbilityResourceByCoefficientCalculationPart', '{763d871b}': 'AbilityResourceByCoefficientCalculationPart', 'BuffCounterByCoefficientCalculationPart': 'BuffCounterByCoefficientCalculationPart', '{4ad0847a}': 'BuffCounterByCoefficientCalculationPart', 'BuffCounterByNamedDataValueCalculationPart': 'BuffCounterByNamedDataValueCalculationPart', '{7af9aae9}': 'BuffCounterByNamedDataValueCalculationPart', 'ByCharLevelBreakpointsCalculationPart': 'ByCharLevelBreakpointsCalculationPart', '{5cf69ece}': 'ByCharLevelBreakpointsCalculationPart', 'ByCharLevelFormulaCalculationPart': 'ByCharLevelFormulaCalculationPart', '{2421b258}': 'ByCharLevelFormulaCalculationPart', 'ByCharLevelInterpolationCalculationPart': 'ByCharLevelInterpolationCalculationPart', '{15fecdbc}': 'ByCharLevelInterpolationCalculationPart', 'ByItemEpicnessCountCalculationPart': 'ByItemEpicnessCountCalculationPart', '{663d5e00}': 'ByItemEpicnessCountCalculationPart', 'ClampSubPartsCalculationPart': 'ClampSubPartsCalculationPart', '{803dae4c}': 'ClampSubPartsCalculationPart', 'CooldownMultiplierCalculationPart': 'CooldownMultiplierCalculationPart', '{1ebf4049}': 'CooldownMultiplierCalculationPart', 'EffectValueCalculationPart': 'EffectValueCalculationPart', '{8bc08357}': 'EffectValueCalculationPart', 'ExponentSubPartsCalculationPart': 'ExponentSubPartsCalculationPart', '{202bfbf6}': 'ExponentSubPartsCalculationPart', 'NamedDataValueCalculationPart': 'NamedDataValueCalculationPart', '{332eb441}': 'NamedDataValueCalculationPart', 'NumberCalculationPart': 'NumberCalculationPart', '{9ef92080}': 'NumberCalculationPart', 'ProductOfSubPartsCalculationPart': 'ProductOfSubPartsCalculationPart', '{ad106e67}': 'ProductOfSubPartsCalculationPart', 'StatByCoefficientCalculationPart': 'StatByCoefficientCalculationPart', '{5815b0a9}': 'StatByCoefficientCalculationPart', 'StatByNamedDataValueCalculationPart': 'StatByNamedDataValueCalculationPart', '{5f5c70a4}': 'StatByNamedDataValueCalculationPart', 'StatBySubPartCalculationPart': 'StatBySubPartCalculationPart', '{cd156c7f}': 'StatBySubPartCalculationPart', 'StatEfficiencyPerHundred': 'StatEfficiencyPerHundred', '{05abdfab}': 'StatEfficiencyPerHundred', 'SubPartScaledProportionalToStat': 'SubPartScaledProportionalToStat', '{995bf516}': 'SubPartScaledProportionalToStat', 'SumOfSubPartsCalculationPart': 'SumOfSubPartsCalculationPart', '{84a63373}': 'SumOfSubPartsCalculationPart', '{4750ceb6}': 'h_4750ceb6', '{e9a3c91d}': 'h_e9a3c91d', '{f3cbe7b2}': 'h_f3cbe7b2'}
        #self.populate_types()

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