import os
import re
import ujson
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class ItemsProcessor:
    def __init__(self, version, output_dir, lang, items, strings):
        self.lang = lang
        self.items = items
        self.strings_raw = strings
        self.strings = strings

        self.output_dir = os.path.join(output_dir, f"lol-items/{version}")

        self.output_filepath = f"{self.output_dir}/{lang}.json"
        self.var_values = {}

        self.__filter_items()
        self.__filter_strings()
        self.__filter_overlaps()

        self.__process_values()

        success_return = {
            'status': 1,
            'data': self.strings
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, sort_keys=True)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)
    
    def __get_string(self, string):
        return get_string(self.strings_raw, string)

    def __filter_array(self, arr, pattern, is_string=False):
        def recursive_replace(input_string):
            def replace_callback(matches):
                key = matches[1].strip().lower().replace('_@champrange@', '_1')
                string = self.__get_string(key)
                if string is not False:
                    return recursive_replace(string)
                else:
                    return matches.group(0)
            
            return re.sub(r'{{\s*(.*?)\s*}}', replace_callback, input_string, flags=re.IGNORECASE)

        filtered_strings = {key: value for key, value in arr.items() if re.match(pattern, key)}

        for key, value in list(filtered_strings.items()):
            matches = re.match(pattern, key)
            if matches:
                number = matches.group(1)
                del filtered_strings[key]

                if is_string:
                    if int(number) in (1101, 1102, 1103) and self.__get_string(f"generatedtip_item_{number}_tooltipextended") != '':
                        value = self.__get_string(f"generatedtip_item_{number}_tooltipshopextended")
                    elif int(number) in (1101, 1102, 1103) and self.__get_string(f"generatedtip_item_{number}_tooltipshopextended") != '':
                        value = self.__get_string(f"generatedtip_item_{number}_tooltipshopextended")

                    value = recursive_replace(value)

                filtered_strings[int(number)] = value

        return filtered_strings
    
    def __filter_items(self):
        for key, value in list(self.items.items()):
            if re.match(r'^\{[0-9a-f]{8}\}$', key) and "itemID" in value:
                if hash_fnv1a("items/" + str(value["itemID"])) == key:
                    self.items["Items/" + str(value["itemID"])] = value
                    del self.items[key]

        self.items = self.__filter_array(self.items, r'^Items/(\d+)$')

    def __filter_strings(self):
        for key, value in self.items.items():
            xxhash39 = hash_xxhash("generatedtip_item_" + str(key) + "_tooltipshop", 39)
            xxhash40 = hash_xxhash("generatedtip_item_" + str(key) + "_tooltipshop", 40)

            if xxhash39 in self.strings:
                self.strings["generatedtip_item_" + str(key) + "_tooltipshop"] = self.strings[xxhash39]
                del self.strings[xxhash39]

            if xxhash40 in self.strings:
                self.strings["generatedtip_item_" + str(key) + "_tooltipshop"] = self.strings[xxhash40]
                del self.strings[xxhash40]

        self.strings = self.__filter_array(self.strings, r'^generatedtip_item_(\d+)_tooltipshop$', True)

    def __filter_overlaps(self):
        keys_to_remove_from_array1 = set(self.items.keys()) - set(self.strings.keys())
        keys_to_remove_from_array2 = set(self.strings.keys()) - set(self.items.keys())

        for key in keys_to_remove_from_array1:
            del self.items[key]

        for key in keys_to_remove_from_array2:
            del self.strings[key]
    
    def __process_values(self):
        def recursive_replace(key, input_string):
            def replace_callback(matches):
                replacement = '@' + matches.group(2) + '@'

                if matches.group(2) == 'spell.PuppyControllerBuff:TreatXP':
                    return '80'
                elif matches.group(2) == 'spell.PuppyControllerBuff:FirstMonsterBonusXP':
                    return '150'

                var_name = matches.group(2).lower().split('*')[0].split('.')[0]
                var_mod = matches.group(2).split('*')[1] if '*' in matches.group(2) else '1'

                if var_mod == '100%':
                    var_mod = 100

                try:
                    var_mod = float(var_mod)
                except:
                    var_mod = 1

                if var_name not in self.var_values[key] and hash_fnv1a(var_name) in self.var_values[key]:
                    var_name = hash_fnv1a(var_name)

                if 'm' + var_name not in self.var_values[key] and hash_fnv1a('m' + var_name) in self.var_values[key]:
                    var_name = hash_fnv1a('m' + var_name)

                if var_name in self.var_values[key]:
                    if isinstance(self.var_values[key][var_name], (int, float)):
                        replacement = round_number(float(self.var_values[key][var_name]) * var_mod, 5, True)
                    else:
                        replacement = self.var_values[key][var_name]

                if var_name == 'value' and var_name not in self.var_values[key]:
                    replacement = '0'

                return replacement

            return re.sub(r'(@)(.*?)(@)', replace_callback, input_string, flags=re.IGNORECASE)
    
        for itemID, itemValues in self.items.items():
            self.var_values[itemID] = {}

            if 'mItemCalculations' not in self.items[itemID] and '{0ac4f0d5}' in self.items[itemID]:
                self.items[itemID]['mItemCalculations'] = self.items[itemID]['{0ac4f0d5}']
                itemValues['mItemCalculations'] = itemValues['{0ac4f0d5}']

            for itemValues_key, itemValues_value in itemValues.items():
                if isinstance(itemValues_value, (int, float)):
                    itemValues_key_lower = itemValues_key.lower()
                    self.var_values[itemID][itemValues_key_lower] = itemValues_value
                    self.var_values[itemID][hash_fnv1a(itemValues_key_lower)] = itemValues_value

                    if re.match(r'^m[A-Z]', itemValues_key):
                        self.var_values[itemID][itemValues_key_lower[1:]] = itemValues_value
                        self.var_values[itemID][hash_fnv1a(itemValues_key_lower[1:])] = itemValues_value

                    if itemValues_key_lower == "price":
                        self.var_values[itemID]['value'] = itemValues_value

                if "mEffectAmount" in itemValues:
                    for mEffectAmount_key, mEffectAmount_value in enumerate(itemValues["mEffectAmount"]):
                        self.var_values[itemID][f'effect{mEffectAmount_key + 1}amount'] = mEffectAmount_value
                        self.var_values[itemID][hash_fnv1a(f'effect{mEffectAmount_key + 1}amount')] = mEffectAmount_value

                if "mDataValues" in itemValues:
                    for mDataValues_value in itemValues["mDataValues"]:
                        mDataValues_name_lower = mDataValues_value['mName'].lower()

                        if "mValue" in mDataValues_value:
                            self.var_values[itemID][mDataValues_name_lower] = mDataValues_value['mValue']
                            self.var_values[itemID][hash_fnv1a(mDataValues_name_lower)] = mDataValues_value['mValue']
                        else:
                            self.var_values[itemID][mDataValues_name_lower] = 0
                            self.var_values[itemID][hash_fnv1a(mDataValues_name_lower)] = 0

            if not 'mItemCalculations' in itemValues and getf(itemValues, "StringCalculations"):
                itemValues['mItemCalculations'] = getf(itemValues, "StringCalculations")
            elif 'mItemCalculations' in itemValues and getf(itemValues, "StringCalculations"):
                itemValues['mItemCalculations'].update(getf(itemValues, "StringCalculations"))
            
            if 'mItemCalculations' in itemValues:
                for mItemCalculations_key, mItemCalculations_value in itemValues['mItemCalculations'].items():
                    # if mItemCalculations_key not in ['MythicPassiveBonus', 'ChampRange', 'ChampLevelReached', 'CurrentMythicBonus']:

                    bin_definitions = BinDefinitions(self.strings_raw, self.var_values[itemID], itemValues['mItemCalculations'])
                    self.var_values[itemID][mItemCalculations_key.lower()] = bin_definitions.parse_values(mItemCalculations_value)
            
            #if itemID == 223084:
            #    print("Values: " + str(self.var_values[itemID]))
            #    print("String: " + str(self.strings[itemID]))
        
        for key, value in self.strings.items():
            replacements = [
                ("item_range_type_melee_dynamic", "item_range_type_melee"),
                ("item_range_type_melee_dynamic_b", "item_range_type_melee_b"),
                ("item_range_type_melee_dynamic_c", "item_range_type_melee_c"),
                ("item_range_type_melee_dynamic_d", "item_range_type_melee_d"),
            ]

            for dynamic_key, melee_key in replacements:
                dynamic_string = self.__get_string(dynamic_key)
                melee_string = self.__get_string(melee_key)

                if dynamic_string is not False and melee_string is not False:
                    if dynamic_string in self.strings[key] and melee_string not in self.strings[key]:
                        value = value.replace(dynamic_string, melee_string)

            replacements2 = [
                ("MeleeRangedSplitB", "item_range_type_melee_b"),
                ("MeleeRangedSplitC", "item_range_type_melee_c"),
                ("MeleeRangedSplitD", "item_range_type_melee_d"),
                ("MeleeRangedSplit", "item_range_type_melee"),
            ]

            for dynamic_key, melee_key in replacements2:
                melee_string = self.__get_string(melee_key)

                if dynamic_key in self.strings[key] and melee_string is not False:
                    if melee_string not in self.strings[key]:
                        value = re.sub(f'@{dynamic_key}@', melee_string, value, flags=re.IGNORECASE)

            self.strings[key] = recursive_replace(key, value)

            matches = re.search(r'<mainText>(.*?)<\/mainText>', self.strings[key], re.IGNORECASE)

            if matches:
                self.strings[key] = matches.group(1)

            self.strings[key] = {
                'epicness': self.var_values[key].get('epicness', 0),
                'desc': self.strings[key]
            }

            if ("mRequiredAlly" in self.items[key] and self.items[key]["mRequiredAlly"] == "Ornn") or ("mItemGroups" in self.items[key] and "Items/ItemGroups/OrnnItems" in self.items[key]["mItemGroups"]):
                self.strings[key]["ornn"] = self.items[key]["recipeItemLinks"][0].replace("Items/", "")

            if "mItemDataClient" in self.items[key]:
                if "InventoryIconLarge" in self.items[key]["mItemDataClient"]:
                    self.strings[key]["icon"] = os.path.splitext(os.path.basename(self.items[key]["mItemDataClient"]["InventoryIconLarge"].lower()))[0]

                if self.items[key]["mItemDataClient"].get("mTooltipData", {}).get("mLocKeys", {}).get("keyColloquialism"):
                            colloq = self.__get_string(self.items[key]["mItemDataClient"]["mTooltipData"]["mLocKeys"]["keyColloquialism"])

                            if colloq is not False:
                                self.strings[key]["colloq"] = colloq