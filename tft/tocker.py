import os
import ujson
from utils import *
from stats import *

class TFTTockerRoundsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.tft_data = tft_data
        self.round_flavors = {}

        self.output_dict = {}

        self.__get_flavors()
        self.__get_rounds()

        self.output_dir = os.path.join(output_dir, f"tft-tocker/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        success_return = {
            'status': 1,
            'data': self.output_dict
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, indent=4)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_flavors(self):
        flavors = self.tft_data['{5d32c638}']['mConstants']

        for id, flavor in flavors.items():
            id = id.replace('_Spawn', '')
            flavor = self.__get_string(flavor['mValue'])

            self.round_flavors[id] = flavor
    
    def __get_rounds(self):
        round_ids = self.tft_data['{f8f86709}']['{d1edd5db}']
        
        for round_id in round_ids:
            self.__get_round(round_id)

    def __get_round(self, round_id):
        round_root = self.tft_data[round_id]
        
        round_name = getf(round_root, 'name')
        round_units = getf(round_root, '{bfad234f}')

        self.output_dict[round_name] = {}
        self.output_dict[round_name]['units'] = []

        self.output_dict[round_name]['desc'] = self.round_flavors[round_name]

        for unit in round_units:
            unit_id = getf(unit, 'Character')
            unit_level = getf(unit, 'level', 0)
            unit_items = getf(unit, 'items', [])

            temp_unit = {
                'id': unit_id.replace('TFTDebug_Dummy', 'TFT_TrainingDummy'),
                'level': unit_level,
                'items': unit_items
            }

            self.output_dict[round_name]['units'].append(temp_unit)