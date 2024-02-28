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

    def __get_champion_list(self):
        current_set_id = self.tft_data["{9fcfd7a6}"]["{0d43af66}"]
        character_list_id = self.tft_data[current_set_id]["tftCharacterLists"][0]
        return self.tft_data[character_list_id]['characters']
    
    def __get_champion(self, id):
        print(r'https://raw.communitydragon.org/latest/game/' + id.lower() + '.cdtb.bin.json')
        champion_data = requests.get(r'https://raw.communitydragon.org/latest/game/' + id.lower() + '.cdtb.bin.json')
        print(champion_data.json())
