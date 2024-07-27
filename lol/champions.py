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
    
    def __get_spells_values(self, champion_data):
        spells_values = {}

        def add_spell_value(spell_dict, key, value):
            spell_dict[key] = value
            spell_dict[hash_fnv1a(key)] = value

        for spell_record in champion_data.values():
            spell_type = getf(spell_record, '__type', '')
            if spell_type != 'SpellObject':
                continue

            spell_data = getf(spell_record, 'mSpell')
            spell_id = getf(spell_record, 'mScriptName', '').lower()

            if not spell_data or not spell_id:
                continue
            
            spells_values[spell_id] = {}

            spell_params = {
                'castrange': getf(spell_data, 'castRange', [0] * 7),
                'cooldowntime': getf(spell_data, 'cooldownTime', [0] * 7),
                'cooldown': getf(spell_data, 'cooldownTime', [0] * 7),
                'maxammo': getf(spell_data, 'mMaxAmmo', [0] * 7),
                'ammorechargetime': getf(spell_data, 'mAmmoRechargeTime', [0] * 7),
                'cost': [0] + getf(spell_data, 'mana', [0] * 7) + [0]
            }

            for param, value in spell_params.items():
                add_spell_value(spells_values[spell_id], param, value)

            m_effect_amount = getf(spell_data, 'mEffectAmount', [])
            for effect_key, effect_value in enumerate(m_effect_amount):
                effect_name = f'effect{effect_key + 1}amount'
                values = getf(effect_value, 'value', [0] * 7)
                add_spell_value(spells_values[spell_id], effect_name, values)

            m_data_values = getf(spell_data, 'mDataValues', [])
            for data_value in m_data_values:
                m_name = getf(data_value, 'mName', '').lower()
                m_values = getf(data_value, 'mValues', [0] * 7)
                if m_name:
                    add_spell_value(spells_values[spell_id], m_name, m_values)

            m_item_calculations = getf(spell_data, 'mSpellCalculations', {})
            for spell_level in range(7):
                spell_values_level = {key: value[spell_level] for key, value in spells_values[spell_id].items()}

                for effect_key, effect_value in m_item_calculations.items():
                    if effect_key.lower() not in spells_values[spell_id]:
                        add_spell_value(spells_values[spell_id], effect_key.lower(), [0] * 7)

                    bin_definitions = BinDefinitions(self.strings_raw, spell_values_level, m_item_calculations)
                    spells_values[spell_id][effect_key.lower()][spell_level] = bin_definitions.parse_values(effect_value)
                    spells_values[spell_id][hash_fnv1a(effect_key.lower())][spell_level] = spells_values[spell_id][effect_key.lower()][spell_level]

            #print(spell_id)
            #print(spells_values[spell_id])
        return spells_values
    
    def __get_champion(self, champion_id, champion_data):
        #if champion_id != 'Characters/Jayce':
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
        
        spells_values = self.__get_spells_values(champion_data)
        
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

        self.__get_spell(num_id, champion_data, spells_values, spell_names[0], 'p')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[1], 'q')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[2], 'w')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[3], 'e')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[4], 'r')

    def __get_spell(self, num_id, champion_data, spells_values, spell_record_path, letter):
        #print(letter)

        spell_record_path = spell_record_path.replace('Characters/FiddleSticks', 'Characters/Fiddlesticks')

        spell_record = getf(champion_data, spell_record_path, {})
        spell_id = getf(spell_record, 'mScriptName', '').lower()
        
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


        spell_icons = getf(m_spell, 'mImgIconName', [])
        spell_icons = [image_to_png(icon) for icon in spell_icons]
        spell_icons = list(dict.fromkeys(spell_icons))


        output_spell = {
            'name': spell_name,
            #'desc': self.__desc_recursive_replace(spell_desc_main, num_id)
            'desc': self.__generate_desc(self.__desc_recursive_replace(spell_desc_main, num_id), spell_id, spells_values),
            'icons': spell_icons
        }

        self.output_dict[num_id]['abilities'][letter].append(output_spell)

    def __generate_desc(self, desc, spell_id, effects):
        def replace_callback(matches):
            nonlocal spell_id
            current_spell_id = spell_id
            search_result = matches.group(2).lower()
            replacement = '@' + search_result + '@'

            if search_result.startswith('spell.'):
                search_result = search_result.replace('spell.', '')
                current_spell_id = search_result.split(':')[0]
                search_result = search_result.split(':')[1]

            #print(current_spell_id, search_result)

            var_name = search_result.split('*')[0].split('.')[0]
            var_mod = search_result.split('*')[1] if '*' in search_result else '1'

            if var_mod == '100%':
                var_mod = 100

            try:
                var_mod = float(var_mod)
            except:
                var_mod = 1

            replacement = getf(effects[current_spell_id], var_name)

            if replacement == None:
                return '@' + matches.group(2) + '@'
            else:
                replacement = replacement[1]

            if isinstance(replacement, (int, float)):
                replacement = round_number(float(replacement) * var_mod, 5, True)

            return replacement

        desc = re.sub(r' size=\'\d+\'', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(<br>){3,}', '<br><br>', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(^(<br>)+)|((<br>)+$)', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'@spell\.[a-z]+([QWER]):hotkey@', '\\1', desc, flags=re.IGNORECASE)
        desc = re.sub(r'@SpellModifierDescriptionAppend@', '', desc, flags=re.IGNORECASE)

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)