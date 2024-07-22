import os
import re
import ujson
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class ItemsProcessor:
    def __init__(self, version, output_dir, lang, maps, modes, strings):
        self.version = version
        self.lang = lang
        self.maps = maps
        self.modes = modes
        self.strings_raw = strings

        self.items = {}
        self.output_dict = {}

        self.output_dir = os.path.join(output_dir, f"lol-items/{self.version}")

        self.output_filepath = f"{self.output_dir}/{lang}.json"

        self.__populate_items()
        self.__process_values()

        success_return = {
            'status': 1,
            'data': dict(sorted(self.output_dict.items()))
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, sort_keys=True)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)
    
    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_items_file(self):
        temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', self.version)
        temp_cache_file = f"{temp_cache_dir}/items.bin.json"

        if os.path.isfile(temp_cache_file):
            try:
                with open(temp_cache_file, encoding='utf-8') as f:
                    return ujson.load(f)
            except Exception as e:
                pass

        urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
        final_url = get_final_url(self.version, urls)

        if not final_url:
            print(f"Items file not found: {self.version}.")
            return
        
        try:
            items_response = requests.get(final_url)

            os.makedirs(temp_cache_dir, exist_ok=True)
            with open(temp_cache_file, 'wb') as output_file:
                output_file.write(items_response.content)

            return ujson.loads(items_response.content)
        except requests.RequestException as e:
            print(f"An error occurred (item file): {e}")
        return
    
    def __get_mode_items(self, map_key, current_map):
        map_root_path = self.modes[map_key]['path']
        map_root = getf(current_map, map_root_path, {})
        item_lists = getf(map_root, "itemLists", [])

        items = []

        for item_list_id in item_lists:
            item_list_root = getf(current_map, item_list_id, {})
            item_list = getf(item_list_root, "mItems", [])
            items = items + item_list

        return list(set(items))
    
    def __populate_items(self):
        items = self.__get_items_file()

        if not items:
            return
        
        item_list_with_modes = {}

        for map_key in self.maps.keys():
            current_map = self.maps[map_key]

            if not current_map:
                continue

            mode_items = self.__get_mode_items(map_key, current_map)

            for item in mode_items:
                if item not in item_list_with_modes:
                    item_list_with_modes[item] = []

                item_list_with_modes[item].append(map_key)

        for item_key, item_data in items.items():
            item_id = getf(item_data, "itemID")

            if not item_id:
                continue

            if re.match(r'^\{[0-9a-f]{8}\}$', item_key):
                if hash_fnv1a(f'Items/{str(item_id)}') == item_key:
                    item_key = f'Items/{str(item_id)}'

            item_modes = getf(item_list_with_modes, item_key)

            if item_modes:
                item_data['lr_modes'] = item_modes
                self.items[item_id] = item_data
    
    def __desc_recursive_replace(self, desc):
        def replace_callback(matches):
            key = matches[1].strip().lower().replace('_@champrange@', '_1')
            str = self.__get_string(key)
            return self.__desc_recursive_replace(str)
        
        return re.sub(r'{{\s*(.*?)\s*}}', replace_callback, desc, flags=re.IGNORECASE)
    
    def __beautify_desc(self, desc):
        desc = re.sub(r'(<br>){3,}', '<br><br>', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(^(<br>)+)|((<br>)+$)', '', desc, flags=re.IGNORECASE)

        desc = re.sub(r'(<br>)+(?=(<rules>|<flavortext>|<section>))', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=<rules>)(<br>)+', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=<flavortext>)(<br>)+', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=<section>)(<br>)+', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=</rules>)(<br>)+', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=</flavortext>)(<br>)+', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(?<=</section>)(<br>)+', '', desc, flags=re.IGNORECASE)

        desc = re.sub(r'(<br>)+(?=<li>)', '<br>', desc, flags=re.IGNORECASE)

        desc = re.sub(r'<flavortext></flavortext>', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'<section></section>', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'<rules></rules>', '', desc, flags=re.IGNORECASE)
        return desc
    
    def __get_desc_raw(self, item_id):
        desc = self.__get_string(f'generatedtip_item_{item_id}_tooltipshop')

        if not desc or int(item_id) in (1101, 1102, 1103):
            extended_key1 = f"generatedtip_item_{item_id}_tooltipextended"
            extended_key2 = f"generatedtip_item_{item_id}_tooltipshopextended"

            if self.__get_string(extended_key1):
                desc = self.__get_string(extended_key1)
            elif self.__get_string(extended_key2):
                desc = self.__get_string(extended_key2)

        if desc == '':
            m_data_client = getf(self.items[item_id], 'mItemDataClient', {})

            m_dynamic_tooltip_key = getf(m_data_client, 'mDynamicTooltip', '')
            m_dynamic_tooltip = self.__get_string(m_dynamic_tooltip_key)

            m_description_key = getf(m_data_client, 'mDescription', '')
            m_description = self.__get_string(m_description_key)

            if m_dynamic_tooltip:
                desc = m_dynamic_tooltip
            elif m_description:
                desc = m_description

        desc = self.__desc_recursive_replace(desc)

        replacements = [
            ("item_range_type_melee_dynamic", "item_range_type_melee"),
            ("item_range_type_melee_dynamic_b", "item_range_type_melee_b"),
            ("item_range_type_melee_dynamic_c", "item_range_type_melee_c"),
            ("item_range_type_melee_dynamic_d", "item_range_type_melee_d"),
        ]

        for dynamic_key, melee_key in replacements:
            dynamic_string = self.__get_string(dynamic_key)
            melee_string = self.__get_string(melee_key)

            if dynamic_string and melee_string:
                if dynamic_string in desc and melee_string not in desc:
                    desc = desc.replace(dynamic_string, melee_string)

        main_text = re.search(r'<mainText>(.*?)<\/mainText>', desc, re.IGNORECASE)

        if main_text:
            desc = main_text.group(1)

        return desc
    
    def __process_values(self):
        for item_id, item_values in self.items.items():

            # Processing values

            item_calc = {}

            for effect_key, effect_value in item_values.items():
                if isinstance(effect_value, (int, float)):
                    effect_key_lower = effect_key.lower()
                    item_calc[effect_key_lower] = effect_value
                    item_calc[hash_fnv1a(effect_key_lower)] = effect_value

                    if re.match(r'^m[A-Z]', effect_key):
                        item_calc[effect_key_lower[1:]] = effect_value
                        item_calc[hash_fnv1a(effect_key_lower[1:])] = effect_value

            m_data_values = getf(item_values, 'mDataValues', [])
            for data_value in m_data_values:
                m_name = getf(data_value, 'mName')
                m_value = getf(data_value, 'mValue', 0)
                
                if m_name:
                    item_calc[m_name.lower()] = m_value
                    item_calc[hash_fnv1a(m_name)] = m_value

            m_effect_amount = getf(item_values, 'mEffectAmount', [])
            for effect_key, effect_value in enumerate(m_effect_amount):
                item_calc[f'effect{effect_key + 1}amount'] = effect_value

            m_item_calculations = getf(item_values, 'mItemCalculations', {})
            m_item_calculations.update(getf(item_values, 'StringCalculations', {}))
            for effect_key, effect_value in m_item_calculations.items():
                bin_definitions = BinDefinitions(self.strings_raw, item_calc, m_item_calculations)
                item_calc[effect_key.lower()] = bin_definitions.parse_values(effect_value)

            # Generating output

            desc = self.__get_desc_raw(item_id)
            desc = self.__generate_desc(desc, item_calc)

            item_name_key = getf(item_values, 'mDisplayName', '')
            item_name = self.__get_string(item_name_key)

            if not item_name and item_name_key == '':
                continue
            elif not item_name:
                item_name = item_name_key

            self.output_dict[item_id] = {
                'rank': getf(item_values, 'epicness', 0),
                'modes': self.items[item_id]['lr_modes'],
                'name': item_name,
                'desc': self.__beautify_desc(desc)
            }

            required_ally = getf(item_values, 'mRequiredAlly', '')
            if required_ally:
                self.output_dict[item_id]['requiredAlly'] = required_ally


            required_champion = getf(item_values, 'mRequiredChampion', '')
            if required_champion:
                self.output_dict[item_id]['requiredChampion'] = required_champion


            recipe = getf(item_values, 'recipeItemLinks')
            if recipe:
                self.output_dict[item_id]['recipe'] = [int(recipe_item_link.replace('Items/', '')) for recipe_item_link in recipe]


            price = getf(item_values, 'price')
            if price:
                self.output_dict[item_id]['price'] = price


            if required_ally == 'Ornn' or 'Items/ItemGroups/OrnnItems' in getf(item_values, 'mItemGroups', []):
                self.output_dict[item_id]['isMasterwork'] = True


            m_data_client = getf(item_values, 'mItemDataClient', {})

            icon_large = getf(m_data_client, 'InventoryIconLarge')
            if icon_large:
                self.output_dict[item_id]['iconGenerated'] = os.path.splitext(os.path.basename(icon_large.lower()))[0]

            icon = getf(m_data_client, 'inventoryIcon')
            if icon:
                self.output_dict[item_id]['icon'] = image_to_png(icon.lower())

            
            m_tooltip_data = getf(m_data_client, 'mTooltipData', {})
            m_loc_keys = getf(m_tooltip_data, 'mLocKeys', {})

            colloq_key = getf(m_loc_keys, 'keyColloquialism')
            if colloq_key:
                self.output_dict[item_id]["colloq"] = self.__get_string(colloq_key)

    
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

            if 'm' + var_name not in effects and hash_fnv1a('m' + var_name) in effects:
                var_name = hash_fnv1a('m' + var_name)

            replacement = getf(effects, var_name, replacement)

            if isinstance(replacement, (int, float)):
                replacement = round_number(float(replacement) * var_mod, 5, True)

            return replacement
        
        if '@spell.PuppyControllerBuff' in desc:
            desc = desc.replace('@spell.PuppyControllerBuff:TreatXP@', '80')
            desc = desc.replace('@spell.PuppyControllerBuff:FirstMonsterBonusXP@', '150')

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)