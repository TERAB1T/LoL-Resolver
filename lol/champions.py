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
    
    def __get_champion(self, champion_id, champion_data):
        #if champion_id != 'Characters/Alistar':
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
        print(letter)

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
        spell_desc_main = self.__get_string(getf(m_loc_keys, "keyTooltip", getf(m_loc_keys, "keySummary")))

        output_spell = {
            'name': spell_name,
            'desc': spell_desc_main
        }

        self.output_dict[num_id]['abilities'][letter].append(output_spell)