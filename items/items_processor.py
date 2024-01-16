import os
import re
import json
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class ItemsProcessor:
    def __init__(self, version, output_dir, lang, items, strings):
        self.lang = lang
        self.items = items
        self.stringsRaw = strings
        self.strings = strings
        self.bin_definitions = BinDefinitions()

        self.output_dir = os.path.join(output_dir, f"items/{version}")

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
        output_json = json.dumps(success_return, ensure_ascii=False, separators=(',', ':'))

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)
    
    def __get_string(self, string):
        return get_string(self.stringsRaw, string)

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
                    if int(number) in (1101, 1102, 1103) and self.__get_string(f"generatedtip_item_{number}_tooltipextended") is not False:
                        value = self.__get_string(f"generatedtip_item_{number}_tooltipextended")

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

    def __parse_item_values(self, var_values, all_calculations, current_block, key=0):
        return_value = ""

        if not isinstance(current_block, (list, dict)):
            return_value = current_block
        elif current_block['__type'] == 'GameCalculation':
            mFormulaParts = {}
            for i, value in enumerate(current_block['mFormulaParts']):
                mFormulaParts[i] = str(round_number(self.__parse_item_values(var_values, all_calculations, value, i), 5, True))

            return_value = ' '.join(mFormulaParts.values())

            if 'mMultiplier' in current_block:
                mMultiplier = self.__parse_item_values(var_values, all_calculations, current_block['mMultiplier'])

                try:
                    mMultiplier = float(mMultiplier)
                    return_value = float(return_value)
                except:
                    pass

                if isinstance(return_value, (int, float)):
                    return_value = round_number(return_value * mMultiplier, 5)

            if 'mDisplayAsPercent' in current_block:
                if isinstance(return_value, (int, float)):
                    return_value = str_ireplace('@NUMBER@', round_number(return_value * 100, not_none(current_block.get('mPrecision'), 5)), self.__get_string('number_formatting_percentage_format'))
                else:
                    def callback_for_numbers(matches):
                        number = float(matches.group(1))
                        return str_ireplace('@NUMBER@', round_number(number * 100, 5, True), self.__get_string('number_formatting_percentage_format'))

                    return_value = re.sub(r'^([0-9]+(\.[0-9]+)*)', callback_for_numbers, return_value)

        elif current_block['__type'] == 'ByCharLevelInterpolationCalculationPart':
            if 'mStartValue' not in current_block:
                return_value = not_none(current_block.get('mEndValue'), '0')
            else:
                if key == 0:
                    return_value = self.__get_string("tooltip_statsuidata_formulapartrangestyle")
                else:
                    return_value = self.__get_string("tooltip_statsuidata_formulapartrangestylebonus")

                return_value = str_ireplace('@OpeningTag@', '<scaleLevel>', return_value)
                return_value = str_ireplace('@RangeStart@', round_number(float(current_block['mStartValue']), 5), return_value)
                return_value = str_ireplace('@RangeEnd@', round_number(float(current_block['mEndValue']), 5), return_value)
                return_value = str_ireplace('@Icon@', '%i:scaleLevel%', return_value)
                return_value = str_ireplace('@ClosingTag@', '</scaleLevel>', return_value)

        elif current_block['__type'] == 'NamedDataValueCalculationPart':
            return_value = 0

            if key == 0:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstyle")
            else:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonus")

            return_value = str_ireplace('@OpeningTag@', "", return_value)
            return_value = str_ireplace('@IconModifier@', '', return_value)
            return_value = str_ireplace('@Icon@', "", return_value)
            return_value = str_ireplace('@ClosingTag@', "", return_value)

            data_value = current_block['mDataValue'].lower()
            if data_value in var_values:
                return_value = str_ireplace('@Value@', round_number(var_values[data_value], 5), return_value)
            else:
                return_value = str_ireplace('@Value@', 0, return_value)
        
        elif current_block['__type'] == 'NumberCalculationPart':
            return_value = current_block['mNumber']

        elif current_block['__type'] == 'EffectValueCalculationPart':
            return_value = var_values['effect' + str(current_block['mEffectIndex']) + 'amount']

        elif current_block['__type'] == 'StatByNamedDataValueCalculationPart' or current_block['__type'] == 'StatByCoefficientCalculationPart' or current_block['__type'] == 'StatBySubPartCalculationPart':
            current_stat = not_none(current_block.get('mStat'), 0)

            if key == 0:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
            else:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

            if 'mStatFormula' in current_block:
                return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
            else:
                return_value = str_ireplace('@IconModifier@', '', return_value)

            return_value = str_ireplace('@OpeningTag@', stats[current_stat]['openingTag'], return_value)

            if current_block['__type'] == 'StatByNamedDataValueCalculationPart':
                value = var_values[current_block['mDataValue'].lower()]
                try:
                    value = float(value) * 100
                except:
                    pass
                return_value = str_ireplace('@Value@', round_number(value, 5), return_value)
            elif current_block['__type'] == 'StatByCoefficientCalculationPart':
                value = current_block['mCoefficient']
                try:
                    value = float(value) * 100
                except:
                    pass
                return_value = str_ireplace('@Value@', round_number(value, 5), return_value)
            elif current_block['__type'] == 'StatBySubPartCalculationPart':
                value = self.__parse_item_values(var_values, all_calculations, current_block['mSubpart'], key)
                try:
                    value = float(value) * 100
                except:
                    pass
                return_value = str_ireplace('@Value@', round_number(value, 5), return_value)

            return_value = str_ireplace('@Icon@', stats[current_stat]['icon'], return_value)
            return_value = str_ireplace('@ClosingTag@', stats[current_stat]['closingTag'], return_value)

        elif current_block['__type'] == 'AbilityResourceByCoefficientCalculationPart':
            if key == 0:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstylepercent")
            else:
                return_value = self.__get_string("tooltip_statsuidata_formulapartstylebonuspercent")

            if 'mStatFormula' in current_block:
                return_value = str_ireplace('@IconModifier@', self.__get_string('tooltip_statsuidata_' + stat_types[current_block['mStatFormula']] + 'iconmodifier'), return_value)
            else:
                return_value = str_ireplace('@IconModifier@', '', return_value)

            return_value = str_ireplace('@OpeningTag@', '<scalemana>', return_value)

            value = current_block['mCoefficient']
            try:
                value = float(value) * 100
            except:
                pass

            return_value = str_ireplace('@Value@', round_number(value, 5), return_value)
            return_value = str_ireplace('@Icon@', '%i:scaleMana%', return_value)
            return_value = str_ireplace('@ClosingTag@', '</scalemana>', return_value)

        elif current_block['__type'] == 'ByCharLevelBreakpointsCalculationPart':
            if key == 0:
                return_value = self.__get_string("tooltip_statsuidata_formulapartrangestyle")
            else:
                return_value = self.__get_string("tooltip_statsuidata_formulapartrangestylebonus")

            if 'mLevel1Value' not in current_block:
                current_block['mLevel1Value'] = 0

            return_value = str_ireplace('@OpeningTag@', '<scaleLevel>', return_value)
            return_value = str_ireplace('@RangeStart@', round_number(float(current_block['mLevel1Value']), 5), return_value)
            return_value = str_ireplace('@Icon@', '%i:scaleLevel%', return_value)
            return_value = str_ireplace('@ClosingTag@', '</scaleLevel>', return_value)

            if 'mBreakpoints' in current_block:
                last_level = 18
                end_value = current_block['mLevel1Value']

                for m_breakpoint in reversed(current_block['mBreakpoints']):
                    current_value = not_none(m_breakpoint.get('{d5fd07ed}'), not_none(m_breakpoint.get('{57fdc438}'), 0))
                    diff = last_level - m_breakpoint['mLevel'] + 1
                    end_value += diff * current_value
                    last_level -= diff

                return_value = str_ireplace('@RangeEnd@', round_number(end_value, 5), return_value)
            else:
                return_value = str_ireplace('@RangeEnd@', round_number(current_block['{02deb550}'] * 17 + current_block['mLevel1Value'], 5), return_value)

        elif current_block['__type'] == 'ProductOfSubPartsCalculationPart':
            m_part1 = self.__parse_item_values(var_values, all_calculations, current_block['mPart1'])
            m_part2 = self.__parse_item_values(var_values, all_calculations, current_block['mPart2'])

            try:
                m_part1 = float(m_part1)
                m_part2 = float(m_part2)
            except:
                pass

            if isinstance(m_part1, (int, float)) and isinstance(m_part2, (int, float)):
                return_value = round_number(m_part1 * m_part2, 5)
            else:
                return_value = 0

        elif current_block['__type'] == 'SumOfSubPartsCalculationPart':
            if len(current_block['mSubparts']) == 1:
                return_value = self.__parse_item_values(var_values, all_calculations, current_block['mSubparts'][0])
            else:
                summ = 0

                for value in current_block['mSubparts']:
                    current_value = self.__parse_item_values(var_values, all_calculations, value)

                    if not isinstance(current_value, (int, float)):
                        summ = 0
                        break
                    else:
                        summ += current_value

                return_value = summ

        elif current_block['__type'] == 'GameCalculationModified':
            multiplier = self.__parse_item_values(var_values, all_calculations, current_block['mMultiplier'])
            modified_block = self.__parse_item_values(var_values, all_calculations, all_calculations[current_block['mModifiedGameCalculation']])

            try:
                multiplier = float(multiplier)
            except:
                matches = re.match(r"^([0-9\.]+)", multiplier)
                if matches:
                    multiplier = float(matches.group(1))
                else:
                    multiplier = 1

            def callback_for_numbers(matches):
                number = float(matches.group(1))
                result = number * multiplier
                return round_number(result, 5, True)

            return_value = re.sub(r'([0-9]+(\.[0-9]+)*)', callback_for_numbers, str(modified_block), flags=re.IGNORECASE)

        elif current_block['__type'] == '{f3cbe7b2}':
            return_value = self.__parse_item_values(var_values, all_calculations, all_calculations[current_block['{88536426}']])

        elif current_block['__type'] == 'BuffCounterByCoefficientCalculationPart' or current_block['__type'] == 'BuffCounterByNamedDataValueCalculationPart' or current_block['__type'] == '{803dae4c}' or current_block['__type'] == '{663d5e00}':
            return_value = 0

        else:
            return_value = current_block

        return return_value
    
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
            
            if 'mItemCalculations' in itemValues:
                for mItemCalculations_key, mItemCalculations_value in itemValues['mItemCalculations'].items():
                    # if mItemCalculations_key not in ['MythicPassiveBonus', 'ChampRange', 'ChampLevelReached', 'CurrentMythicBonus']:

                    self.var_values[itemID][mItemCalculations_key.lower()] = self.__parse_item_values(self.var_values[itemID], itemValues['mItemCalculations'], mItemCalculations_value)
            
            #if itemID == 223084:
            #    print("Values: " + str(self.var_values[itemID]))
            #    print("String: " + str(self.strings[itemID]))
        
        for key, value in self.strings.items():

            replacements = [
                ("item_range_type_melee_dynamic", "item_range_type_melee"),
                ("item_range_type_melee_dynamic_b", "item_range_type_melee_b"),
                ("item_range_type_melee_dynamic_c", "item_range_type_melee_c")
            ]

            for dynamic_key, melee_key in replacements:
                dynamic_string = self.__get_string(dynamic_key)
                melee_string = self.__get_string(melee_key)

                if dynamic_string is not False and melee_string is not False:
                    if dynamic_string in self.strings[key] and melee_string not in self.strings[key]:
                        value = value.replace(dynamic_string, melee_string)

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