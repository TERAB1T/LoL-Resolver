import os
import re
import ujson
from utils import *
from stats import *

class TFTTraitsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, traits, trait_units, unit_props, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.unit_props = unit_props

        self.tft_data = tft_data
        self.traits = traits
        self.trait_units = trait_units

        self.output_dict = {}
        self.__get_traits()

        self.output_dir = os.path.join(output_dir, f"tft-traits/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        success_return = {
            'status': 1,
            'data': self.output_dict
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, sort_keys=True)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __get_traits(self):
        pass