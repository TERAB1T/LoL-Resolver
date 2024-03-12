import os
import re
import ujson
from utils import *
from stats import *

class TFTItemsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, items, type, unit_props, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.type = type
        self.unit_props = unit_props

        self.tft_data = tft_data
        self.items = items['items']
        self.augments = items['augments']

        self.output_dict = {}

        if self.type == 'items':
            self.output_dir = os.path.join(output_dir, f"tft-items/{version}")
            self.__get_items()
        elif self.type == 'augments':
            self.output_dir = os.path.join(output_dir, f"tft-augments/{version}")
            self.__get_augments()

        self.output_filepath = f"{self.output_dir}/{lang}.json"

        success_return = {
            'status': 1,
            'data': self.output_dict
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, sort_keys=True)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)
    
    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_items(self):
        for item_id, item_data in self.items.items():
            pass

    def __get_augments(self):
        for aug_id, aug_data in self.augments.items():
            aug_name_id = aug_data.get("mDisplayNameTra", aug_data.get(hash_fnv1a("mDisplayNameTra")))
            aug_name = self.__get_string(aug_name_id)

            aug_desc_id = aug_data.get("mDescriptionNameTra", aug_data.get(hash_fnv1a("mDescriptionNameTra")))
            aug_desc = self.__get_string(aug_desc_id)

            aug_icon = aug_data.get("mIconPath", aug_data.get(hash_fnv1a("mIconPath")))
            aug_icon_large = aug_data.get("{d434d358}", aug_icon)

            aug_unit = aug_data.get("{f0021999}")
            aug_traits = aug_data.get("AssociatedTraits", aug_data.get(hash_fnv1a("AssociatedTraits")))

            aug_tags = aug_data.get("ItemTags", aug_data.get(hash_fnv1a("ItemTags")))
            aug_tier = -1

            if aug_tags:
                if '{d11fd6d5}' in aug_tags:
                    aug_tier = 1
                elif '{ce1fd21c}' in aug_tags:
                    aug_tier = 2
                elif '{cf1fd3af}' in aug_tags:
                    aug_tier = 3

            aug_effects_raw = aug_data.get("effectAmounts", aug_data.get(hash_fnv1a("effectAmounts")))
            aug_effects = self.unit_props.copy()

            if aug_effects_raw:
                for effect in aug_effects_raw:
                    effect_name = effect.get("name", effect.get(hash_fnv1a("name")))
                    effect_value = effect.get("value", effect.get(hash_fnv1a("value"), 0))

                    if effect_name:
                        aug_effects[effect_name.lower()] = effect_value

            self.output_dict[aug_id.lower()] = {
                'id': aug_id,
                'name': aug_name,
                'desc': self.__generate_desc(aug_desc, aug_effects),
                'icon': aug_icon.lower(),
                'iconLarge': aug_icon_large.lower(),
                'tier': aug_tier
            }

            if aug_unit:
                self.output_dict[aug_id.lower()]['unit'] = aug_unit.lower()

            if aug_traits:
                self.output_dict[aug_id.lower()]['traits'] = [self.tft_data[trait]['mName'].lower() for trait in aug_traits]

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

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)