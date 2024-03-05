import os
import re
import json
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
            'data': self.output_dict
        }
        output_json = json.dumps(success_return, ensure_ascii=False, separators=(',', ':'))

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)


    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_unit(self, unit_id, unit_data):
        #if unit_id != 'Characters/TFT10_Ahri':
        #    return

        #print(unit_id)
        
        unit_id_trimmed = unit_id.split("/")[1].lower()
        root_record = unit_data[f'{unit_id}/CharacterRecords/Root']

        if not root_record.get("spellNames"):
            return

        spell_record = unit_data.get(f'{unit_id}/Spells/{root_record["spellNames"][0]}')

        if not spell_record or not spell_record.get("mSpell") or not spell_record["mSpell"]["mClientData"]["mTooltipData"].get("mLocKeys") or not spell_record["mSpell"].get("mDataValues"):
            return

        spell_desc_main_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLocKeys"]["keyTooltip"]
        spell_desc_main = self.__get_string(spell_desc_main_raw)

        if 'TFT10_Headliner_TRA@' in spell_desc_main:
            headliner_id = f'tft10_headliner_{unit_id_trimmed}'
            spell_desc_main = str_ireplace('@TFTUnitProperty.:TFT10_Headliner_TRA@', self.__get_string(headliner_id), spell_desc_main)
            spell_desc_main = str_ireplace('@TFTUnitProperty.unit:TFT10_Headliner_TRA@', self.__get_string(headliner_id), spell_desc_main)

        if '@TFTUnitProperty.' in spell_desc_main:
            spell_desc_main = str_ireplace('@TFTUnitProperty.unit:', '@', spell_desc_main)
            spell_desc_main = str_ireplace('@TFTUnitProperty.:', '@', spell_desc_main)

        spell_desc_scaling_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLists"]["LevelUp"]

        var_values = {}

        for data_value in spell_record["mSpell"]["mDataValues"]:
            if data_value.get("mName") and data_value.get("mValues"):
                var_values[data_value["mName"].lower()] = [round(data_value["mValues"][i], 5) for i in range(5)]
                var_values[hash_fnv1a(data_value["mName"].lower())] = var_values[data_value["mName"].lower()]

        champion_stats = {
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
        }

        spell_calculations_raw = spell_record["mSpell"].get("mSpellCalculations")
        spell_calculations = {}

        for key, value in var_values.items():
            spell_calculations[key.lower()] = self.__process_value_array([value[i] for i in range(1, 4)])

        spell_calculations.update(self.unit_properties)

        if spell_calculations_raw:
            for spell_calculations_key, spell_calculations_value in spell_calculations_raw.items():
                spell_calculations[spell_calculations_key.lower()] = []
                for i in range(1, 4):
                    current_var_values = {key: value[i] for key, value in var_values.items()}
                    current_champion_stats = {key: value[i] for key, value in champion_stats.items()}
                    bin_definitions = BinDefinitions(self.strings_raw, current_var_values, spell_calculations_raw, current_champion_stats, True)
                    calculated_value = bin_definitions.parse_values(spell_calculations_value)
                    spell_calculations[spell_calculations_key.lower()].append(calculated_value if not isinstance(calculated_value, (int, float)) and '%' in calculated_value else float(calculated_value))
                spell_calculations[spell_calculations_key.lower()] = self.__process_value_array(spell_calculations[spell_calculations_key.lower()])
                spell_calculations[hash_fnv1a(spell_calculations_key.lower())] = spell_calculations[spell_calculations_key.lower()]

        spell_desc_scaling = self.__process_spell_scaling(spell_desc_scaling_raw, var_values)
        self.output_dict[unit_id_trimmed] = self.__generate_champion_tooltip(f"{spell_desc_main}{spell_desc_scaling}", spell_calculations, var_values)
        
        #print(champion_stats)
        #print(spell_calculations)

        #print(champion_stats)
        #print(data_values)
        #print(self.strings[champion_id_trimmed])
        #print(spell_desc_scaling_raw)

        #with open(r"C:/Users/Alex/Desktop/tft-test/" + id.lower() + '.cdtb.bin.json', 'w') as file:
        #    file.write(champion_data.text)

        #print(champion_data.json())
    
    def __process_spell_scaling(self, spell_desc_main_raw, var_values):
        scaling_elements = spell_desc_main_raw.get("elements")
        if not scaling_elements:
            return ""
        
        return_array = []

        for element in scaling_elements:
            style = element.get("Style")
            current_string = '<scalingcontainer><scalingblock>' + self.__get_string(element["nameOverride"]) + '</scalingblock>'

            if not style:
                values = [str(round_number(var_values[element["type"].lower()][i], 2)) for i in range(1, 4)]
                current_string += f'<scalingblock>[{"/".join(values)}]</scalingblock>'
            elif style == 1:
                multiplier = element.get("multiplier", 1)
                values = [str(round_number(var_values[element["type"].lower()][i] * multiplier, 2)) for i in range(1, 4)]
                current_string += f'<scalingblock>[{"/".join(values)}%]</scalingblock>'

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
        
    def __generate_champion_tooltip(self, spell_desc_main, spell_calculations, var_values):
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

            if var_name not in spell_calculations and hash_fnv1a(var_name) in spell_calculations:
                var_name = hash_fnv1a(var_name)

            if var_name in spell_calculations:
                decimal_places = 0

                if var_name in var_values:
                    decimal_places = 2

                if isinstance(spell_calculations[var_name], (int, float)):
                    replacement = round_number(float(spell_calculations[var_name]) * var_mod, decimal_places, True)
                else:
                    if '/' in spell_calculations[var_name] and not '%' in spell_calculations[var_name]:
                        replacement = '/'.join([round_number(float(x) * var_mod, decimal_places, True) for x in spell_calculations[var_name].split('/')])
                    elif '/' in spell_calculations[var_name] and '%' in spell_calculations[var_name]:
                        replacement = re.sub('%/', '/', spell_calculations[var_name])
                    else:
                        replacement = spell_calculations[var_name]

            if var_name == 'value' and var_name not in spell_calculations:
                replacement = '0'

            #print(matches.group(2), spell_calculations.get(var_name), replacement)
            return replacement
        
        return re.sub(r'(@)(.*?)(@)', replace_callback, spell_desc_main, flags=re.IGNORECASE)