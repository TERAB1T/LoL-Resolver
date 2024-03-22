import os
import re
import ujson
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class TFTUnitsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, unit_list, unit_properties, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings

        self.hp_coef = [0.7, 1, 1.8, 3.24, 5.832]
        self.ad_coef = [0.5, 1, 1.5, 2.25, 3.375]
        if re.match(r'^\d+\.\d+$', str(version)) and normalize_game_version(version) < 12.14:
            self.ad_coef = self.hp_coef

        self.output_dict = {}
        self.output_dir = os.path.join(output_dir, f"tft-units/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        self.tft_data = tft_data
        self.unit_list = unit_list
        self.unit_properties = unit_properties

        for key, value in self.unit_list.items():
            self.__get_unit(key, value)

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
    
    def __get_unit(self, unit_id, unit_data):
        #if unit_id != 'Characters/TFT8_Ashe':
        #    return

        print(unit_id)
        
        unit_id_trimmed = unit_id.split("/")[1].lower()

        root_record_path = f'{unit_id}/CharacterRecords/Root'
        root_record = unit_data.get(root_record_path, unit_data.get(hash_fnv1a(root_record_path)))
        if not root_record or not root_record.get("spellNames"):
            return

        spell_record_path = f'{unit_id}/Spells/{root_record["spellNames"][0]}'
        spell_record = unit_data.get(spell_record_path, unit_data.get(hash_fnv1a(spell_record_path)))

        if not spell_record or not spell_record.get("mSpell") or\
           not spell_record["mSpell"].get("mClientData") or\
           not spell_record["mSpell"]["mClientData"].get("mTooltipData") or\
           not spell_record["mSpell"]["mClientData"]["mTooltipData"].get("mLocKeys") or\
           not spell_record["mSpell"].get("mDataValues"):
            return

        spell_name = self.__get_string(spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLocKeys"]["keyName"])
        spell_desc_main_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLocKeys"]["keyTooltip"]
        spell_desc_main = self.__get_string(spell_desc_main_raw)

        if 'TFT10_Headliner_TRA@' in spell_desc_main:
            headliner_id = f'tft10_headliner_{unit_id_trimmed}'
            spell_desc_main = str_ireplace('@TFTUnitProperty.:TFT10_Headliner_TRA@', self.__get_string(headliner_id), spell_desc_main)
            spell_desc_main = str_ireplace('@TFTUnitProperty.unit:TFT10_Headliner_TRA@', self.__get_string(headliner_id), spell_desc_main)

        spell_desc_scaling_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLists"]["LevelUp"]
        scaling_levels = 1 + spell_desc_scaling_raw.get("levelCount", 3)

        unit_shop_data = self.tft_data.get(root_record.get('mShopData', root_record.get(hash_fnv1a("mShopData"))))

        var_values = {}

        for data_value in spell_record["mSpell"]["mDataValues"]:
            if data_value.get("mName") and data_value.get("mValues"):
                var_values[data_value["mName"].lower()] = [round(data_value["mValues"][i], 5) for i in range(5)]
                var_values[hash_fnv1a(data_value["mName"].lower())] = var_values[data_value["mName"].lower()]

        unit_stats = {
            0:  [100.0] * 5, # ability power
            1:  [round(root_record.get('baseArmor', 0), 5)] * 5, # armor
            2:  [round(root_record.get('baseDamage', 0) * self.ad_coef[i], 5) for i in range(5)], # attack damage
            3:  [round(root_record.get('attackSpeed', 0), 5)] * 5, # attack speed
            5:  [round(root_record.get('baseSpellBlock', 0), 5)] * 5, # magic resistance
            6:  [round(root_record.get('baseMoveSpeed', 0), 5)] * 5, # move speed
            7:  [round(root_record.get('baseCritChance', 0), 5)] * 5, # crit chance
            8:  [round(root_record.get('critDamageMultiplier', 0), 5)] * 5, # crit damage
            11: [round(root_record.get('baseHP', 0) * self.hp_coef[i], 5) for i in range(5)], # max health
            28: [round(root_record.get('attackRange', 0), 5)] * 5, # attack range
            33: [1] * 5, # dodge chance
        }

        spell_calc_raw = spell_record["mSpell"].get("mSpellCalculations")
        if not spell_calc_raw:
            spell_calc_raw = spell_record["mSpell"].get(hash_fnv1a("mSpellCalculations"))
        spell_calc = {}
        spell_style = {}

        for key, value in var_values.items():
            spell_calc[key.lower()] = self.__process_value_array([value[i] for i in range(1, scaling_levels)])

        spell_calc.update(self.unit_properties)

        if spell_calc_raw:
            for spell_calc_key, spell_calc_value in spell_calc_raw.items():
                spell_calc[spell_calc_key.lower()] = []
                for i in range(1, scaling_levels):
                    current_var_values = {key: value[i] for key, value in var_values.items()}
                    current_unit_stats = {key: value[i] for key, value in unit_stats.items()}
                    bin_definitions = BinDefinitions(self.strings_raw, current_var_values, spell_calc_raw, current_unit_stats, True)

                    parsed_bin = bin_definitions.parse_values(spell_calc_value)

                    if isinstance(parsed_bin, dict):
                        calculated_value = parsed_bin['value']

                        if re.match(r'^\d+\.\d+$', str(self.version)) and normalize_game_version(self.version) < 13.12:
                            spell_style[spell_calc_key.lower()] = {
                                'tag': parsed_bin['tag'],
                                'icon': parsed_bin['icon']
                            }
                    else:
                        calculated_value = parsed_bin

                    spell_calc[spell_calc_key.lower()].append(calculated_value if not isinstance(calculated_value, (int, float)) and '%' in calculated_value else float(calculated_value))
                spell_calc[spell_calc_key.lower()] = self.__process_value_array(spell_calc[spell_calc_key.lower()])

                spell_calc[hash_fnv1a(spell_calc_key.lower())] = spell_calc[spell_calc_key.lower()]

                if spell_calc_key.lower() in spell_style:
                    spell_style[hash_fnv1a(spell_calc_key.lower())] = spell_style[spell_calc_key.lower()]

        spell_desc_scaling = self.__process_spell_scaling(spell_desc_scaling_raw, var_values)

        self.output_dict[unit_id_trimmed] = {
            'id': unit_id.split("/")[1],
            'name': self.__get_string(unit_shop_data["mDisplayNameTra"]),
            'cost': root_record.get('tier', 0),
            'icon': unit_shop_data.get("{dac11dd4}", "").lower(),
            'tileSmall': unit_shop_data.get("{466dc3cc}", "").lower(),
            'tileLarge': unit_shop_data.get("{16071366}", "").lower(),
        }

        if "{b6b01440}" in root_record:
            self.output_dict[unit_id_trimmed]['role'] = self.__get_string(self.tft_data[root_record["{b6b01440}"]]["{5969040c}"])

        self.output_dict[unit_id_trimmed]['stats'] = {
            'health': round_number(unit_stats[11][1], 2),
            'startingMana': round_number(root_record.get('mInitialMana', unit_data.get(hash_fnv1a('mInitialMana'), 0)), 2),
            'maxMana': round_number(root_record["primaryAbilityResource"].get("arBase", 100), 2),
            'attackDamage': round_number(unit_stats[2][1], 2),
            'abilityPower': round_number(unit_stats[0][1], 2),
            'armor': round_number(unit_stats[1][1], 2),
            'magicResist': round_number(unit_stats[5][1], 2),
            'attackSpeed': round_number(unit_stats[3][1], 2),
            'range': int(unit_stats[28][1] / 180),
        }

        if "mLinkedTraits" in root_record:
            self.output_dict[unit_id_trimmed]['traits'] = [self.tft_data[trait["TraitData"]]["mName"].lower() for trait in root_record["mLinkedTraits"]]

        self.output_dict[unit_id_trimmed]['ability'] = {
            'name': spell_name,
            'desc': self.__generate_unit_tooltip(f"{spell_desc_main}{spell_desc_scaling}", spell_calc, var_values, spell_style),
            'icon': unit_shop_data.get("{df0ad83b}", "").lower(),
        }

        print(self.output_dict[unit_id_trimmed])
        print('\n----\n')
        
        #print(champion_stats)
        #print(spell_calculations)

        #print(self.output_dict[unit_id_trimmed])
        #print(data_values)
        #print(spell_desc_scaling_raw)

        #with open(r"C:/Users/Alex/Desktop/tft-test/" + id.lower() + '.cdtb.bin.json', 'w') as file:
        #    file.write(champion_data.text)

        #print(champion_data.json())
    
    def __process_spell_scaling(self, spell_desc_scaling_raw, var_values):
        scaling_elements = spell_desc_scaling_raw.get("elements")
        scaling_levels = 1 + spell_desc_scaling_raw.get("levelCount", 3)
        if not scaling_elements:
            return ""
        
        return_array = []

        for element in scaling_elements:
            style = element.get("Style")
            current_string = '<scalingcontainer><scalingblock>' + self.__get_string(element["nameOverride"]) + '</scalingblock>'

            if not style:
                values = [str(round_number(var_values[element["type"].lower()][i], 2)) for i in range(1, scaling_levels)]
                current_string += f"<scalingblock>[{'/'.join(values)}]</scalingblock>"
            elif style == 1:
                multiplier = element.get("multiplier", 1)
                values = [str(round_number(var_values[element["type"].lower()][i] * multiplier, 2)) for i in range(1, scaling_levels)]
                current_string += f"<scalingblock>[{str_ireplace('@NUMBER@', '/'.join(values), self.__get_string('number_formatting_percentage_format'))}]</scalingblock>"

            return_array.append(current_string + '</scalingcontainer>')

        return '<hr>' + ''.join(return_array)

    def __process_value_array(self, arr):
        arr = [round_number(x, 5, True) for x in arr]

        if all(x == arr[0] for x in arr):
            try:
                arr[0] = float(arr[0])
            except:
                pass

            return arr[0]
        else:
            return '/'.join(arr)
        
    def __generate_unit_tooltip(self, spell_desc_main, spell_calc, var_values, spell_style = {}):
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

            if var_name not in spell_calc and hash_fnv1a(var_name) in spell_calc:
                var_name = hash_fnv1a(var_name)

            if var_name in spell_calc:
                decimal_places = 0

                if var_name in var_values:
                    decimal_places = 2

                if isinstance(spell_calc[var_name], (int, float)):
                    replacement = round_number(float(spell_calc[var_name]) * var_mod, decimal_places, True)
                else:
                    if '/' in spell_calc[var_name] and not '%' in spell_calc[var_name]:
                        replacement = '/'.join([round_number(float(x) * var_mod, decimal_places, True) for x in spell_calc[var_name].split('/')])
                    elif '/' in spell_calc[var_name] and '%' in spell_calc[var_name]:
                        replacement = re.sub(' *%/', '/', spell_calc[var_name])
                    else:
                        replacement = spell_calc[var_name]

            if var_name == 'value' and var_name not in spell_calc:
                replacement = '0'

            if var_name in spell_style:
                current_style = spell_style[var_name]
                replacement = f"<{current_style['tag']}>{replacement} %i:{current_style['icon']}%</{current_style['tag']}>"

            #print(matches.group(2), spell_calculations.get(var_name), replacement)
            return replacement
        
        if '@TFTUnitProperty.' in spell_desc_main:
            spell_desc_main = str_ireplace('@TFTUnitProperty.unit:', '@', spell_desc_main)
            spell_desc_main = str_ireplace('@TFTUnitProperty.:', '@', spell_desc_main)

        return re.sub(r'(@)(.*?)(@)', replace_callback, spell_desc_main, flags=re.IGNORECASE)