import os
import re
import ujson
from utils import *
from stats import *

class SwarmAugmentsProcessor:
    def __init__(self, version, output_dir, lang, swarm_data, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings

        self.swarm_data = swarm_data

        self.output_dict = {}
        self.output_dir = os.path.join(output_dir, f"swarm-augments/{version}")
        self.__get_augments()

        self.output_filepath = f"{self.output_dir}/{lang}.json"

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
    
    def __get_augments(self):
        augment_entries = [value for key, value in self.swarm_data.items() if value.get('__type') == 'AugmentData' or value.get('__type') == '{6dfab860}']
        spellobject_entries = {key: value for key, value in self.swarm_data.items() if value.get('__type') == 'SpellObject' or value.get('__type') == '{5e7e5a06}'}

        for augment in augment_entries:
            self.output_dict[augment['AugmentNameId'].lower()] = {
                'id': augment['AugmentNameId'],
                'name': self.__get_string(augment['NameTra']),
                'desc': self.__prepare_desc(spellobject_entries, augment),
                'icon': image_to_png(augment['AugmentSmallIconPath'].lower()),
                'iconLarge': image_to_png(augment['AugmentLargeIconPath'].lower()),
                'tier': getf(augment, "rarity", 0)
            }

    def __prepare_desc(self, spellobject_entries, augment):
        desc = self.__get_string(augment['DescriptionTra'])

        spellobject_id = getf(augment, "RootSpell", '')
        spellobject = getf(spellobject_entries, spellobject_id)

        if spellobject:
            mSpell = getf(spellobject, "mSpell", {})
            mDataValues = getf(mSpell, "mDataValues")

            if mDataValues:
                effects = {}

                for data_value in mDataValues:
                    m_name = getf(data_value, "mName")
                    m_values = getf(data_value, "mValues", [])

                    if m_values and m_values[1]:
                        effects[m_name.lower()] = m_values[1]

                desc = self.__generate_desc(desc, effects)

        return desc
    
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

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)
