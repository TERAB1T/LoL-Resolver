import os
import re
import json
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class TFTUnitsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, strings):
        self.lang = lang
        self.tft_data = tft_data
        self.hp_coef = [0.7, 1, 1.8, 3.24, 5.832]
        self.ad_coef = [0.5, 1, 1.5, 2.25, 3.375]
        self.strings_raw = strings
        self.strings = strings
        self.champion_list = self.__get_champion_list()

        self.output_dir = os.path.join(output_dir, f"tft_units/{version}")

        self.output_filepath = f"{self.output_dir}/{lang}.json"
        self.var_values = {}


        for id in self.champion_list:
            self.__get_champion(id)


        success_return = {
            'status': 1,
            'data': self.strings
        }
        output_json = json.dumps(success_return, ensure_ascii=False, separators=(',', ':'))

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_champion_list(self):
        current_set_id = self.tft_data["{9fcfd7a6}"]["{0d43af66}"]
        character_list_id = self.tft_data[current_set_id]["tftCharacterLists"][0]
        return self.tft_data[character_list_id]['characters']
    
    def __get_champion(self, champion_id):
        #if champion_id != 'Characters/TFT10_Jax':
        #    return

        print(champion_id)
        
        champion_data_url = f'https://raw.communitydragon.org/latest/game/{champion_id.lower()}.cdtb.bin.json'
        champion_data_response = requests.get(champion_data_url)
        champion_data = champion_data_response.json()

        root_record = champion_data[f'{champion_id}/CharacterRecords/Root']

        if not root_record.get("spellNames"):
            return

        spell_record = champion_data.get(f'{champion_id}/Spells/{root_record["spellNames"][0]}')

        if not spell_record or not spell_record.get("mSpell") or not spell_record["mSpell"]["mClientData"]["mTooltipData"].get("mLocKeys") or not spell_record["mSpell"].get("mDataValues"):
            return

        spell_desc_main_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLocKeys"]["keyTooltip"]
        spell_desc_main = self.__get_string(spell_desc_main_raw)

        spell_desc_scaling_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLists"]["LevelUp"]
        spell_desc_scaling = self.__process_spell_scaling(spell_desc_scaling_raw)

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

        if spell_calculations_raw:
            for spell_calculations_key, spell_calculations_value in spell_calculations_raw.items():
                spell_calculations[spell_calculations_key] = []
                for i in range(1, 4):
                    current_var_values = {key: value[i] for key, value in var_values.items()}
                    current_champion_stats = {key: value[i] for key, value in champion_stats.items()}
                    bin_definitions = BinDefinitions(self.strings_raw, current_var_values, spell_calculations_raw, current_champion_stats, True)
                    calculated_value = bin_definitions.parse_values(spell_calculations_value)
                    spell_calculations[spell_calculations_key].append(calculated_value if not isinstance(calculated_value, (int, float)) and '%' in calculated_value else float(calculated_value))
                spell_calculations[spell_calculations_key] = self.__process_value_array(spell_calculations[spell_calculations_key])
        
        #print(champion_stats)
        print(spell_calculations)

        #print(champion_stats)
        #print(data_values)
        #print(spell_desc_main)
        #print(spell_desc_scaling_raw)

        #with open(r"C:/Users/Alex/Desktop/tft-test/" + id.lower() + '.cdtb.bin.json', 'w') as file:
        #    file.write(champion_data.text)

        #print(champion_data.json())
    
    def __process_spell_scaling(self, spell_desc_main_raw):
        pass

    def __process_value_array(self, arr):
        arr = [round_number(x, 0, True) for x in arr]

        if all(x == arr[0] for x in arr):
            return arr[0]
        else:
            return '/'.join(arr)