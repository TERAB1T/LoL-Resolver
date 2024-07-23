import os
import re
import ujson
from utils import *
from stats import *
from bin_definitions import BinDefinitions

class ChampionsProcessor:
    def __init__(self, version, output_dir, lang, champion_list, strings):
        self.version = version
        self.lang = lang
        self.champions = champion_list
        self.strings_raw = strings

        self.output_dict = {}
        self.output_dir = os.path.join(output_dir, f"lol-champions/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        for key, value in self.champions.items():
            self.__get_champion(key, value)

        success_return = {
            'status': 1,
            'data': dict(sorted(self.output_dict.items()))
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, sort_keys=True, indent=4)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)


    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_champion(self, champion_id, champion_data):
        if champion_id != 'Characters/Alistar':
            return

        print(champion_id)
        
        champion_id_trimmed = champion_id.split("/")[1].lower()

        root_record_path = f'{champion_id}/ChampionRecord'
        root_record = getf(champion_data, root_record_path)
        if not root_record:
            return
        
        name = getf(root_record, "name")