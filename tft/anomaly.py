import os
import ujson
from utils import *
from stats import *

class TFTAnomalyProcessor:
    def __init__(self, version, output_dir, lang, tft_data, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings
        self.tft_data = tft_data

        self.output_dict = {}

        self.__get_anomalies()

        self.output_dir = os.path.join(output_dir, f"tft-anomaly/{version}")
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
    
    def __get_anomalies(self):
        tft_data_main = self.tft_data["{9fcfd7a6}"]
        current_set_id = getf(tft_data_main, "mDefaultSetData", getf(tft_data_main, "DefaultSetData"))
        set_root = self.tft_data[current_set_id]

        anomaly_list_id = getf(set_root, "{e6c62bd9}", '')
        anomaly_list_root = getf(self.tft_data, anomaly_list_id, {})
        anomaly_list = getf(anomaly_list_root, "{9a7587b2}", [])

        for anomaly_entry in anomaly_list:
            anomaly_id = getf(anomaly_entry, "{16c534fd}", '')
            anomaly = getf(self.tft_data, anomaly_id)

            if anomaly:
                self.__get_anomaly(anomaly)

    def __get_anomaly(self, anomaly):
        anomaly_id = getf(anomaly, "name")

        strings_path = getf(anomaly, "{900aff58}")
        strings = getf(self.tft_data, strings_path)

        anomaly_name = self.__get_string(getf(strings, "TitleTra"))
        anomaly_subtitle = self.__get_string(getf(strings, "SubtitleTra"))
        anomaly_desc = self.__get_string(getf(strings, "DescriptionTra"))

        effects_raw = getf(anomaly, "effectAmounts")
        item_effects = {}

        if effects_raw:
            for effect in effects_raw:
                effect_name = getf(effect, "name")
                effect_value = getf(effect, "value", 0)
                
                if effect_name:
                    item_effects[effect_name.lower()] = effect_value

        self.output_dict[anomaly_id.lower()] = {
            'id': anomaly_id,
            'name': anomaly_name,
            'subtitle': anomaly_subtitle,
            'desc': self.__generate_desc(anomaly_desc, item_effects),
        }

    def __generate_desc(self, desc, effects):
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

            if var_name not in effects and hash_fnv1a(var_name) in effects:
                var_name = hash_fnv1a(var_name)

            if var_name in effects:
                replacement = round_number(float(effects[var_name]) * var_mod, 2, True)

            if var_name == 'value' and var_name not in effects:
                replacement = '0'

            return replacement
        
        if '@TFTUnitProperty.' in desc:
            desc = re.sub(r'TFTUnitProperty\.[a-z]*:', '', desc, flags=re.IGNORECASE)

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)