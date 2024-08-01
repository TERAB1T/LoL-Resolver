from ..bin_calc import *

class ClampSubPartsCalculationPart(BinCalculation):
    def __init__(self, strings, var_values, all_calculations, champion_stats = {}):
        super().__init__(strings, var_values, all_calculations, champion_stats)

    def calc_string(self, current_block, key):
        floor = current_block.get('mFloor')
        ceiling = current_block.get('mCeiling')
        subparts = current_block.get('mSubparts')

        if subparts and len(subparts) > 0:
            calculated_subparts = self.calc_values(subparts[0], 0, 'string')
            
            return calculated_subparts
        
        return 0
    
    def calc_float(self, current_block, key):
        floor = current_block.get('mFloor')
        ceiling = current_block.get('mCeiling')
        subparts = current_block.get('mSubparts')

        if subparts and len(subparts) > 0:
            calculated_subparts = self.check_dict(self.calc_values(subparts[0], 0, 'float'))

            if floor and calculated_subparts < floor:
                return floor
            
            if ceiling and calculated_subparts > ceiling:
                return ceiling
            
            return calculated_subparts
        
        return 0