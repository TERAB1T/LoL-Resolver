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
        self.ad_hp_coef = [0.7, 1, 1.8, 3.24, 5.832]
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
        if champion_id != 'Characters/TFT10_Garen':
            return
        
        champion_data_url = f'https://raw.communitydragon.org/latest/game/{champion_id.lower()}.cdtb.bin.json'
        champion_data_response = requests.get(champion_data_url)
        champion_data = champion_data_response.json()

        root_record = champion_data[f'{champion_id}/CharacterRecords/Root']
        spell_record = champion_data.get(f'{champion_id}/Spells/{root_record["spellNames"][0]}')

        spell_desc_main_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLocKeys"]["keyTooltip"]
        spell_desc_main = self.__get_string(spell_desc_main_raw)

        spell_desc_coef_raw = spell_record["mSpell"]["mClientData"]["mTooltipData"]["mLists"]["LevelUp"]
        spell_desc_coef = self.__process_spell_coefs(spell_desc_main_raw)

        champion_stats = {
            0: [100.0] * 5, # ability power
            1: [round(root_record['baseArmor'], 2)] * 5, # armor
            2: [round(root_record['baseDamage'] * self.ad_hp_coef[i], 2) for i in range(5)], # attack damage
            3: [round(root_record['attackSpeed'], 2)] * 5, # attack speed
            5: [round(root_record['baseSpellBlock'], 2)] * 5, # magic resistance
            6: [round(root_record['baseMoveSpeed'], 2)] * 5, # move speed
            7: [round(root_record['baseCritChance'], 2)] * 5, # crit chance
            8: [round(root_record['critDamageMultiplier'], 2)] * 5, # crit damage
            11: [round(root_record['baseHP'] * self.ad_hp_coef[i], 2) for i in range(5)], # max health
        }

        print(champion_stats)
        print(spell_desc_main)
        print(spell_desc_coef_raw)

        #with open(r"C:/Users/Alex/Desktop/tft-test/" + id.lower() + '.cdtb.bin.json', 'w') as file:
        #    file.write(champion_data.text)

        #print(champion_data.json())
    
    def __process_spell_coefs(self, spell_desc_main_raw):
        pass