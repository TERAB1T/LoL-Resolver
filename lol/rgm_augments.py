import os
import re
import ujson
from utils import *
from constants import *
from bin_defs.bin_main import BinDefinitions

class RGMAugmentsProcessor:
    def __init__(self, version, output_dir, map_type, lang, data, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings

        self.data = data

        self.output_dict = {}
        self.output_dir = os.path.join(output_dir, f'{map_type}-augments/{version}')
        self.__get_augments()
        #self.__get_announcements()

        self.output_filepath = f"{self.output_dir}/{lang}.json"

        success_return = {
            'status': 1,
            'data': dict(sorted(self.output_dict.items()))
        }
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), sort_keys=True, escape_forward_slashes=False, indent=4)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)

    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __desc_recursive_replace(self, desc):
        def replace_callback(matches):
            key = matches[1].strip().lower()
            str = self.__get_string(key)

            if not str:
                str = f'[[{key}]]'

            return self.__desc_recursive_replace(str)

        desc = re.sub(r'{{\s*(.*?)\s*}}', replace_callback, desc, flags=re.IGNORECASE)
        return desc
    
    def __get_announcements(self):
        augment_entries = [value for key, value in self.data.items() if value.get('__type') == 'AnnouncementDefinition' or value.get('__type') == hash_fnv1a('AnnouncementDefinition')]

        for augment in augment_entries:
            data = getf(augment, 'DefaultData', {})
            desc_key = getf(data, 'TextKey', '')
            desc = self.__get_string(desc_key)

            self.output_dict[desc_key] = {
                'desc': desc
            }
    
    def __get_augments(self):
        augment_entries = []

        for key, value in self.data.items():
            if not isinstance(value, list) and (
                value.get('__type') == 'AugmentData' or value.get('__type') == hash_fnv1a('AugmentData')
            ):
                augment_entries.append(value)

        spellobject_entries = {}

        for key, value in self.data.items():
            if not isinstance(value, list) and (
                value.get('__type') == 'SpellObject' or value.get('__type') == hash_fnv1a('SpellObject')
            ):
                spellobject_entries[key] = value

        for augment in augment_entries:
            self.output_dict[augment['AugmentNameId'].lower()] = {
                'id': augment['AugmentNameId'],
                'name': self.__get_string(augment['NameTra']),
                'desc': self.__prepare_desc(spellobject_entries, augment),
                'icon': image_to_png(getf(augment, 'AugmentSmallIconPath', '').lower()),
                'iconLarge': image_to_png(getf(augment, 'AugmentLargeIconPath', '').lower()),
                'tier': getf(augment, "rarity", 0)
            }

    def __prepare_desc(self, spellobject_entries, augment):
        desc_id = getf(augment, 'AugmentTooltipTra', getf(augment, 'DescriptionTra'))

        desc = self.__get_string(desc_id)
        desc = self.__desc_recursive_replace(desc)
        desc = re.sub(r'@f\d+@', '0', desc, flags=re.IGNORECASE)

        if '@spell.' in desc:
            desc = re.sub(r'@spell\.[^:]+:', '@', desc, flags=re.IGNORECASE)


        spellobject_id = getf(augment, "RootSpell", '')
        spellobject = getf(spellobject_entries, spellobject_id)
        effects = {}

        if spellobject:
            m_spell = getf(spellobject, "mSpell", {})
            m_data_values = getf(m_spell, "mDataValues")
            m_spell_calculations = getf(m_spell, 'mSpellCalculations')

            if m_data_values:
                for data_value in m_data_values:
                    m_name = getf(data_value, "mName")
                    m_values = getf(data_value, "mValues", [])

                    if m_values and m_values[1]:
                        effects[m_name.lower()] = m_values[1]
            
            if m_spell_calculations:
                
                for effect_key, effect_value in m_spell_calculations.items():
                    bin_definitions = BinDefinitions(self.strings_raw, effects, m_spell_calculations)
                    effects[effect_key.lower()] = bin_definitions.calc_values(effect_value)

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

            replacement = getf(effects, var_name, replacement)

            if isinstance(replacement, (int, float)):
                replacement = round_number(float(replacement) * var_mod, 5, True)

            return replacement

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)
