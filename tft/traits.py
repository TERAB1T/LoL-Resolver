import os
import re
import ujson
from utils import *
from stats import *

class TFTTraitsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, traits, trait_units, unit_props, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.unit_props = unit_props

        self.tft_data = tft_data
        self.traits = traits
        self.trait_units = trait_units

        self.output_dict = {}
        self.__get_traits()

        self.output_dir = os.path.join(output_dir, f"tft-traits/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        success_return = {
            'status': 1,
            'data': dict(sorted(self.output_dict.items()))
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_traits(self):
        for trait_id, trait_data in self.traits.items():

            #if trait_id != "TFT11_Bruiser":
            #    continue
            #print(trait_id + '\n')

            if not trait_id.lower() in self.trait_units and trait_id != 'TFT11_Exalted':
                continue

            trait_name_id = getf(trait_data, "mDisplayNameTra")
            trait_name = self.__get_string(trait_name_id)

            effects_main_raw = trait_data.get("{6f4cf34d}", [])
            effects_main = self.unit_props.copy()

            for effect in effects_main_raw:
                effect_amounts = getf(effect, "effectAmounts", [])

                for amount in effect_amounts:
                    effect_name = getf(amount, "name")
                    effect_value = getf(amount, "value", 0)
                    effects_main[effect_name.lower()] = effect_value
            
            effects_bonus_raw = getf(trait_data, "mConditionalTraitSets")
            if not effects_bonus_raw:
                effects_bonus_raw = getf(trait_data, "mTraitSets", [])
            effects_bonus = {}
            breakpoints = []

            is_first_effect = True
            for effect in effects_bonus_raw:
                min_units = getf(effect, "minUnits")
                if not min_units:
                    min_units = getf(effect, "mMinUnits")

                breakpoints.append(min_units)

                effects_bonus[min_units] = {}

                effect_amounts = getf(effect, "effectAmounts", [])

                for amount in effect_amounts:
                    effect_name = getf(amount, "name")
                    effect_value = getf(amount, "value", 0)
                    effects_bonus[min_units][effect_name.lower()] = effect_value

                    if is_first_effect:
                        effects_main[effect_name.lower()] = effect_value
                
                is_first_effect = False

            trait_desc_id = getf(trait_data, "mDescriptionNameTra")
            trait_desc = self.__prepare_desc(self.__get_string(trait_desc_id), effects_main, effects_bonus, breakpoints)

            trait_icon = getf(trait_data, "mIconPath")

            self.output_dict[trait_id.lower()] = {
                'id': trait_id,
                'name': trait_name,
                'desc': trait_desc,
                'icon': image_to_png(trait_icon.lower()),
                'breakpoints': breakpoints
            }

            if trait_id.lower() in self.trait_units:
                self.output_dict[trait_id.lower()]['units'] = self.trait_units[trait_id.lower()]

    def __prepare_desc(self, trait_desc, effects_main, effects_bonus, breakpoints):
        trait_desc = re.sub(r'<expandrow>(.*?)<\/expandrow>', '<row>' + '</row><br><row>'.join(['\\1'] * len(effects_bonus)) + '</row>', trait_desc, flags=re.IGNORECASE)
        count = 0

        def replace_callback(matches):
            nonlocal count
            return_value = matches[1]
            
            min_units = list(effects_bonus)[count]
            effects = list(effects_bonus.values())[count]

            return_value = re.sub(r'@MinUnits@', round_number(min_units, 0, True), return_value, flags=re.IGNORECASE)
            return_value = self.__generate_desc(return_value, effects)

            count += 1
            return return_value

        trait_desc = re.sub(r'@TFTUnitProperty\.[a-z]*:TFT11_Trait_Fortune7Tooltip@', self.__get_string('tft11_fortune_tooltip_tra'), trait_desc, flags=re.IGNORECASE)
        trait_desc = re.sub(r'(?=<row>)(.*?)(?<=<\/row>)', replace_callback, trait_desc, flags=re.IGNORECASE)
        trait_desc = re.sub(r'@MinUnits@', round_number(breakpoints[0], 0, True), trait_desc, flags=re.IGNORECASE)
        return self.__generate_desc(trait_desc, effects_main)
    
    def __generate_desc(self, desc, effects):
        def replace_callback(matches):
            replacement = '@' + matches.group(2) + '@'

            var_name = matches.group(2).lower().split('*')[0].split('.')[0]
            var_mod = matches.group(2).split('*')[1] if '*' in matches.group(2) else '1'

            if var_mod == '100%':
                var_mod = 100

            try:
                var_mod = float(var_mod)
            except:
                var_mod = 1

            if var_name not in effects and hash_fnv1a(var_name) in effects:
                var_name = hash_fnv1a(var_name)

            if var_name in effects:
                replacement = round_number(float(effects[var_name]) * var_mod, 2, True)

            if var_name == 'value' and var_name not in effects:
                replacement = '0'

            return replacement
        
        if '@TFTUnitProperty.' in desc:
            desc = re.sub(r'TFTUnitProperty\.[a-z]*:', '', desc, flags=re.IGNORECASE)

        if '@TFT11_Trait_Inkshadow_Item' in desc:
            desc = re.sub(r'@TFT11_Trait_Inkshadow_Item', '@Item', desc, flags=re.IGNORECASE)

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)