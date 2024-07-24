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
        output_json = ujson.dumps(success_return, ensure_ascii=False, separators=(',', ':'), escape_forward_slashes=False, indent=4)

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.output_filepath, 'w', encoding='utf-8') as output_file:
            output_file.write(output_json)


    def __get_string(self, string):
        return get_string(self.strings_raw, string)
    
    def __desc_recursive_replace(self, desc, num_id):
        def replace_callback(matches):
            key = matches[1].strip().lower()
            key = key.replace('@gamemodeinteger@', '1')

            if num_id == 134: # Syndra
                key = key.replace("@f3@", "0")
            elif num_id == 141: # Kayn
                key = key.replace("@f1@", "0")

            str = self.__get_string(key)

            if not str:
                str = f'[[{key}]]'

            return self.__desc_recursive_replace(str, num_id)
        
        return re.sub(r'{{\s*(.*?)\s*}}', replace_callback, desc, flags=re.IGNORECASE)
    
    def __get_champion(self, champion_id, champion_data):
        #if champion_id != 'Characters/Kayn':
        #    return

        print(champion_id)
        
        champion_id_trimmed = champion_id.split("/")[1].lower()

        root_record_path = f'{champion_id}/CharacterRecords/Root'
        root_record = getf(champion_data, root_record_path)
        if not root_record:
            return
        
        spell_names = getf(root_record, "spellNames")
        if not spell_names:
            return
        else:
            spell_names = [f'{champion_id}/Spells/{spell_name}' for spell_name in spell_names]

        passive_name = getf(root_record, 'mCharacterPassiveSpell')
        if not passive_name:
            return
        else:
            spell_names.insert(0, passive_name)
        
        character_tool_data = getf(root_record, "characterToolData", {})
        num_id = getf(character_tool_data, "championId")
        if not num_id:
            return
        
        self.output_dict[num_id] = {
            'id': champion_id.split("/")[1],
            'name': self.__get_string(getf(root_record, "name")),
            'abilities': {
                'p': [],
                'q': [],
                'w': [],
                'e': [],
                'r': []
            }
        }

        self.__get_spell(num_id, champion_data, spell_names[0], 'p')
        self.__get_spell(num_id, champion_data, spell_names[1], 'q')
        self.__get_spell(num_id, champion_data, spell_names[2], 'w')
        self.__get_spell(num_id, champion_data, spell_names[3], 'e')
        self.__get_spell(num_id, champion_data, spell_names[4], 'r')

    def __get_spell(self, num_id, champion_data, spell_record_path, letter):
        #print(letter)

        spell_record = getf(champion_data, spell_record_path, {})
        
        m_spell = getf(spell_record, "mSpell", {})
        m_client_data = getf(m_spell, "mClientData", {})
        m_tooltip_data = getf(m_client_data, "mTooltipData", {})
        m_loc_keys = getf(m_tooltip_data, "mLocKeys")
        m_lists = getf(m_tooltip_data, "mLists", {})
        m_data_values = getf(m_spell, "mDataValues", [])
        m_spell_calc = getf(m_spell, "mSpellCalculations")

        if not m_loc_keys:
            return
        
        spell_name = self.__get_string(getf(m_loc_keys, "keyName"))
        spell_desc_main = ''

        desc_summary = getf(m_loc_keys, "keySummary")
        desc_tooltip = getf(m_loc_keys, "keyTooltip")
        desc_tooltip_below_line = getf(m_loc_keys, "keyTooltipExtendedBelowLine")
        desc_tooltip_extended = getf(m_loc_keys, "keyTooltipExtended")

        if desc_tooltip_extended:
            spell_desc_main = self.__get_string(desc_tooltip_extended)
        elif desc_tooltip:
            spell_desc_main = self.__get_string(desc_tooltip)
        elif desc_summary:
            spell_desc_main = self.__get_string(desc_summary)

        if desc_tooltip_below_line:
            spell_desc_main += '<br><br>' + self.__get_string(desc_tooltip_below_line)

        output_spell = {
            'name': spell_name,
            'desc': self.__desc_recursive_replace(spell_desc_main, num_id)
        }

        self.output_dict[num_id]['abilities'][letter].append(output_spell)