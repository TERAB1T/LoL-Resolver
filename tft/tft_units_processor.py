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

        self.output_dir = os.path.join(output_dir, f"tft_units/{version}")

        self.output_filepath = f"{self.output_dir}/{lang}.json"
        self.var_values = {}

        # calls

        success_return = {
            'status': 1,
            'data': self.strings
        }
        output_json = json.dumps(success_return, ensure_ascii=False, separators=(',', ':'))

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)