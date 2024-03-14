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

        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'radiants.json'), 'r') as file:
            self.radiants = ujson.load(file)

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
        components = []
        item_ids_lower = [id.lower() for id in self.items.keys()]

        for item_id, item_data in self.items.items():
            item_name_id = item_data.get("mDisplayNameTra", item_data.get(hash_fnv1a("mDisplayNameTra")))
            item_name = self.__get_string(item_name_id)

            item_desc_id = item_data.get("mDescriptionNameTra", item_data.get(hash_fnv1a("mDescriptionNameTra")))
            item_desc = self.__get_string(item_desc_id)

            item_icon = item_data.get("mIconPath", item_data.get(hash_fnv1a("mIconPath")))
            item_unit = item_data.get("{f0021999}")
            item_traits = item_data.get("AssociatedTraits", item_data.get(hash_fnv1a("AssociatedTraits")))

            item_tags = item_data.get("ItemTags", item_data.get(hash_fnv1a("ItemTags")))
            item_type = None
            item_parent = None

            radiant_guess = re.sub(r'(radiant|shadow|_genae)$', '', item_id.lower())
            radiant_guess = re.sub(r'tft(\d+)', 'tft', radiant_guess)

            if item_tags:
                if '{5efd6ee0}' in item_tags:
                    item_type = 'Component'
                elif '{44ace175}' in item_tags:
                    item_type = 'Artifact'
                elif 'Consumable' in item_tags or hash_fnv1a('consumable') in item_tags:
                    item_type = 'Consumable'
                elif '{27557a09}' in item_tags:
                    item_type = 'Support'
                elif '{6ef5c598}' in item_tags:
                    item_type = 'Radiant'
                elif '{ebcd1bac}' in item_tags:
                    item_type = 'Emblem'
                elif '{da7e999a}' in item_tags:
                    item_type = 'Inkshadow'
                elif '{d30ba8ed}' in item_tags:
                    item_type = 'Shadow'
                elif '{47df912f}' in item_tags:
                    item_type = 'Gadgeteen'

                if '{6ef5c598}' in item_tags or '{d30ba8ed}' in item_tags or '{47df912f}' in item_tags:

                    if not 'tft_item_seraphsembrace' in item_ids_lower:
                        self.radiants['TFT5_Item_BlueBuffRadiant'.lower()] = 'tft_item_bluebuff'

                    if item_id.lower() in self.radiants:
                        item_parent = self.radiants[item_id.lower()]
                    elif radiant_guess in item_ids_lower:
                        item_parent = radiant_guess

            item_recipe_raw = item_data.get("mComposition", item_data.get(hash_fnv1a("mComposition")))
            item_recipe = []

            if item_recipe_raw:
                for component_link in item_recipe_raw:
                    component = self.tft_data.get(component_link, self.tft_data.get(hash_fnv1a(component_link)))

                    if component:
                        component_id = component.get("mName", component.get(hash_fnv1a("mName"))).lower()
                        item_recipe.append(component_id)

                        if not component_id in components and component_id in item_ids_lower:
                            components.append(component_id)

            item_effects_raw = item_data.get("effectAmounts", item_data.get(hash_fnv1a("effectAmounts")))
            item_effects = self.unit_props.copy()
            item_stats = []

            if item_effects_raw:
                for effect in item_effects_raw:
                    effect_name = effect.get("name", effect.get(hash_fnv1a("name")))
                    effect_value = effect.get("value", effect.get(hash_fnv1a("value"), 0))
                    effect_format = effect.get("formatString", effect.get(hash_fnv1a("formatString")))

                    if effect_format:
                        item_stat = re.sub(r'@Value', f'@{effect_name}', effect_format, flags=re.IGNORECASE)
                        item_stats.append(item_stat)
                    
                    if effect_name:
                        item_effects[effect_name.lower()] = effect_value

            self.output_dict[item_id.lower()] = {
                'id': item_id,
                'name': item_name,
                'desc': self.__generate_desc(item_desc, item_effects),
                'icon': item_icon.lower()
            }

            if item_unit:
                self.output_dict[item_id.lower()]['unit'] = item_unit.lower()

            if item_traits:
                self.output_dict[item_id.lower()]['traits'] = [self.tft_data[trait]['mName'].lower() for trait in item_traits]

            if item_parent:
                self.output_dict[item_id.lower()]['parent'] = item_parent

            if len(item_recipe):
                if item_recipe[0] in item_ids_lower and item_recipe[1] in item_ids_lower:
                    self.output_dict[item_id.lower()]['recipe'] = item_recipe

                    if not 'spatula' in item_recipe[0] and 'spatula' in item_recipe[1]:
                        item_recipe[0], item_recipe[1] = item_recipe[1], item_recipe[0]
                else:
                    del self.output_dict[item_id.lower()]
                    continue

            if item_type:
                self.output_dict[item_id.lower()]['type'] = item_type
            elif item_id.lower().endswith('spatulaitem'):
                self.output_dict[item_id.lower()]['type'] = 'Emblem'
            elif len(item_recipe):
                self.output_dict[item_id.lower()]['type'] = 'Complete'

            if len(item_stats):
                self.output_dict[item_id.lower()]['stats'] = [self.__generate_desc(item_stat, item_effects) for item_stat in item_stats]

        for component in components:
            component_type = self.output_dict[component].get('type')

            if component_type and component_type == 'Shadow':
                self.output_dict[component]['type'] = 'Shadow Component'
            else:
                self.output_dict[component]['type'] = 'Component'

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