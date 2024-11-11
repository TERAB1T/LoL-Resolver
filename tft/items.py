import os
import re
import ujson
from utils import *
from stats import *

class TFTItemsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, items, item_type, unit_props, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.type = item_type
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
            'data': dict(sorted(self.output_dict.items()))
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, indent=4)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)
    
    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_items(self):
        components = []
        item_ids_lower = [id.lower() for id in self.items.keys()]

        base_stat_format = getf(getf(self.tft_data, '{9fcfd7a6}', {}), '{b1725d57}', {})

        for item_id, item_data in self.items.items():
            item_name_id = getf(item_data, "mDisplayNameTra")
            item_name = self.__get_string(item_name_id)

            item_desc_id = getf(item_data, "mDescriptionNameTra")
            item_desc = self.__get_string(item_desc_id)

            item_icon = getf(item_data, "mIconPath")
            item_unit = getf(item_data, "AssociatedCharacterName")
            item_traits = getf(item_data, "AssociatedTraits")

            item_tags = getf(item_data, "ItemTags")
            item_type = None
            item_parent = None
            item_cost = None

            radiant_guess = re.sub(r'(radiant|shadow|_genae)$', '', item_id.lower())
            radiant_guess = re.sub(r'tft(\d+)', 'tft', radiant_guess)

            if item_tags:
                if 'component' in item_tags or hash_fnv1a('component') in item_tags:
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
                elif '{5b609ae2}' in item_tags:
                    item_type = 'Charm'
                elif 'tft12_item_faerie_' in item_id.lower():
                    item_type = 'Faerie'
                elif '{d3de812d}' in item_tags:
                    item_type = 'Chem-Baron'

                if '{05e9c2cd}' in item_tags:
                    item_type = 'Chem-Baron (Consumable)'
                elif '{7c5b9cc2}' in item_tags:
                    item_type = 'Chem-Baron (Bronze)'
                elif '{99d978bb}' in item_tags:
                    item_type = 'Chem-Baron (Silver)'
                elif '{b25b1dec}' in item_tags:
                    item_type = 'Chem-Baron (Gold)'
                elif '{d28853e6}' in item_tags:
                    item_type = 'Chem-Baron (Prismatic)'

                if item_type in ('Radiant', 'Shadow', 'Gadgeteen', 'Faerie'):
                    if not 'tft_item_seraphsembrace' in item_ids_lower:
                        self.radiants['TFT5_Item_BlueBuffRadiant'.lower()] = 'tft_item_bluebuff'

                    if item_id.lower() in self.radiants:
                        item_parent = self.radiants[item_id.lower()]
                    elif radiant_guess in item_ids_lower:
                        item_parent = radiant_guess

            if item_type == 'Charm':
                shop_data_id = getf(item_data, "ShopData", '')
                shop_data = getf(self.tft_data, shop_data_id, {})
                item_cost = getf(shop_data, "BaseCost", 0)

            item_recipe_raw = getf(item_data, "mComposition")
            item_recipe = []

            if item_recipe_raw:
                for component_link in item_recipe_raw:
                    component = getf(self.tft_data, component_link)

                    if component:
                        component_id = getf(component, "mName").lower()
                        item_recipe.append(component_id)

                        if not component_id in components and component_id in item_ids_lower:
                            components.append(component_id)

            item_effects_raw = getf(item_data, "effectAmounts")
            item_effects_raw_2 = getf(getf(item_data, "constants", {}), '{df085b93}')
            item_effects = self.unit_props.copy()
            item_stats = []

            if item_effects_raw:
                for effect in item_effects_raw:
                    effect_name = getf(effect, "name")
                    effect_value = getf(effect, "value", 0)
                    effect_format = getf(effect, "formatString")

                    if effect_format:
                        item_stat = re.sub(r'@Value', f'@{effect_name}', effect_format, flags=re.IGNORECASE)
                        item_stats.append(item_stat)
                    
                    if effect_name:
                        item_effects[effect_name.lower()] = effect_value
            elif item_effects_raw_2:
                for effect_name, effect_value in item_effects_raw_2.items():
                    item_effects[effect_name.lower()] = getf(effect_value, 'mValue', 0)

                    if effect_name in base_stat_format:
                        item_stat = re.sub(r'@Value', f'@{effect_name}', getf(base_stat_format, effect_name, ''), flags=re.IGNORECASE)
                        item_stats.append(item_stat)

            self.output_dict[item_id.lower()] = {
                'id': item_id,
                'name': item_name,
                'desc': self.__generate_desc(item_desc, item_effects),
                'icon': image_to_png(item_icon.lower())
            }

            if item_unit:
                self.output_dict[item_id.lower()]['unit'] = item_unit.lower()

            if item_traits:
                self.output_dict[item_id.lower()]['traits'] = [self.tft_data[trait]['mName'].lower() for trait in item_traits]

            if item_parent:
                self.output_dict[item_id.lower()]['parent'] = item_parent

            if item_cost or item_cost == 0:
                self.output_dict[item_id.lower()]['cost'] = item_cost

            if item_recipe:
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
            elif item_recipe:
                self.output_dict[item_id.lower()]['type'] = 'Completed'
            elif 'consumable' in item_id.lower():
                self.output_dict[item_id.lower()]['type'] = 'Consumable'

            elif 'junkerking' in item_id.lower():
                self.output_dict[item_id.lower()]['type'] = 'Junker King'

            if item_stats:
                self.output_dict[item_id.lower()]['stats'] = [self.__generate_desc(item_stat, item_effects) for item_stat in item_stats]

        for component in components:
            component_type = self.output_dict[component].get('type')

            if component_type and component_type == 'Shadow':
                self.output_dict[component]['type'] = 'Shadow Component'
            else:
                self.output_dict[component]['type'] = 'Component'

    def __get_augments(self):
        for aug_id, aug_data in self.augments.items():
            aug_name_id = getf(aug_data, "mDisplayNameTra")
            aug_name = self.__get_string(aug_name_id)

            aug_desc_id = getf(aug_data, "mDescriptionNameTra")
            aug_desc = self.__get_string(aug_desc_id)

            aug_icon = getf(aug_data, "mIconPath")
            aug_icon_large = getf(aug_data, "mArmoryIconOverridePath", aug_icon)

            aug_unit = getf(aug_data, "AssociatedCharacterName")
            aug_traits = getf(aug_data, "AssociatedTraits")

            aug_tags = getf(aug_data, "ItemTags")
            aug_tier = -1

            if aug_tags:
                if '{d11fd6d5}' in aug_tags:
                    aug_tier = 1
                elif '{ce1fd21c}' in aug_tags:
                    aug_tier = 2
                elif '{cf1fd3af}' in aug_tags:
                    aug_tier = 3

            aug_effects_raw = getf(aug_data, "effectAmounts")
            aug_effects_raw_2 = getf(getf(aug_data, "constants", {}), '{df085b93}')
            aug_effects = self.unit_props.copy()

            if aug_effects_raw:
                for effect in aug_effects_raw:
                    effect_name = getf(effect, "name")
                    effect_value = getf(effect, "value", 0)

                    if effect_name:
                        aug_effects[effect_name.lower()] = effect_value
            elif aug_effects_raw_2:
                for effect_name, effect_value in aug_effects_raw_2.items():
                    aug_effects[effect_name.lower()] = getf(effect_value, 'mValue', 0)

            self.output_dict[aug_id.lower()] = {
                'id': aug_id,
                'name': aug_name,
                'desc': self.__generate_desc(aug_desc, aug_effects),
                'icon': image_to_png(aug_icon.lower()),
                'iconLarge': image_to_png(aug_icon_large.lower()),
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