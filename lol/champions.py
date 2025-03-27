import os
import re
import ujson
from utils import *
from constants import *
from bin_defs.bin_main import BinDefinitions

class ChampionsProcessor:
    def __init__(self, version, output_dir, lang, champion_list, champion_list_client, strings):
        self.version = version
        self.lang = lang
        self.champions = champion_list
        self.champions_client = champion_list_client
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
    
    def __desc_recursive_replace(self, desc, num_id, letter):
        def replace_callback(matches):
            key = matches[1].strip().lower()
            key = key.replace('@gamemodeinteger@', '1')

            if num_id == 134: # Syndra
                key = key.replace("@f3@", "0")
            elif num_id == 141: # Kayn
                key = key.replace("@f1@", "0")
            elif num_id == 523: # Aphelios
                key = re.sub(r'gunshortdesc_@f(\d+)@', 'gunshortdesc_\\1', key, flags=re.IGNORECASE)

            str = self.__get_string(key)

            if not str:
                str = f'[[{key}]]'

            return self.__desc_recursive_replace(str, num_id, letter)
        
        if num_id == 523: # Aphelios
            desc = re.sub(r'{{\s*apheliosgun_lorename_@f1@\s*}}', '{{apheliosgun_lorename_1}} / {{apheliosgun_lorename_2}} / {{apheliosgun_lorename_3}} / {{apheliosgun_lorename_4}} / {{apheliosgun_lorename_5}}', desc, flags=re.IGNORECASE)
            desc = re.sub(r'{{\s*spell_apheliosr_weaponmod_@f1@\s*}}', '{{spell_apheliosr_weaponmod_1}}{{spell_apheliosr_weaponmod_2}}{{spell_apheliosr_weaponmod_3}}{{spell_apheliosr_weaponmod_4}}{{spell_apheliosr_weaponmod_5}}', desc, flags=re.IGNORECASE)
        
        desc = re.sub(r'{{\s*(.*?)\s*}}', replace_callback, desc, flags=re.IGNORECASE)
        desc = self.__f_vars_replace(desc, num_id, letter)
        return desc
    
    def __get_spells_values(self, champion_data):
        spells_values = {}

        def add_spell_value(spell_dict, key, value):
            spell_dict[key] = value

            if not is_fnv1a(key):
                spell_dict[hash_fnv1a(key)] = value

        for spell_record in champion_data.values():
            if isinstance(spell_record, list):
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
            for spell_level in range(7): #7
                spell_values_level = {key: value[spell_level] for key, value in spells_values[spell_id].items()}

                for effect_key, effect_value in m_item_calculations.items():
                    if effect_key.lower() not in spells_values[spell_id]:
                        add_spell_value(spells_values[spell_id], effect_key.lower(), [0] * 7)

                    bin_definitions = BinDefinitions(self.strings_raw, spell_values_level, m_item_calculations)
                    spells_values[spell_id][effect_key.lower()][spell_level] = bin_definitions.calc_values(effect_value)

                    if not is_fnv1a(effect_key):
                        spells_values[spell_id][hash_fnv1a(effect_key.lower())][spell_level] = spells_values[spell_id][effect_key.lower()][spell_level]

            #print(spell_id)
            #print(spells_values[spell_id])
        return spells_values
    
    def __get_champion(self, champion_id, champion_data):
        #if champion_id != 'Characters/Annie':
        #    return

        #print(champion_id)

        if not '/' in champion_id:
            return
        
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

        passive_name = getf(root_record, 'mCharacterPassiveSpell', '')
        spell_names.insert(0, passive_name)
        
        character_tool_data = getf(root_record, "characterToolData", {})
        num_id = getf(character_tool_data, "championId")
        if not num_id:
            return
        
        primary_ability_resource = getf(root_record, "primaryAbilityResource", {})
        ar_type = getf(primary_ability_resource, "arType", 14)
        
        spells_values = self.__get_spells_values(champion_data)
        spells_values['ar_type'] = ar_type
        
        name_id = getf(root_record, "name").lower()
        title_id = name_id.replace('displayname', 'description')
        bio_id = name_id.replace('displayname', 'lore')

        self.output_dict[num_id] = {
            'id': champion_id.split("/")[1],
            'name': self.__get_string(name_id),
            'title': self.__get_string(title_id),
            'bio': self.__get_string(bio_id),
            'abilities': {
                'p': {
                    'data': []
                },
                'q': {
                    'data': []
                },
                'w': {
                    'data': []
                },
                'e': {
                    'data': []
                },
                'r': {
                    'data': []
                },
            }
        }

        self.__get_client_data(num_id)

        if not 'iconImage' in self.output_dict[num_id]:
            del(self.output_dict[num_id])
            return

        self.__get_spell(num_id, champion_data, spells_values, spell_names[0], 'p')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[1], 'q')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[2], 'w')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[3], 'e')
        self.__get_spell(num_id, champion_data, spells_values, spell_names[4], 'r')


        if num_id == 60: # Elise
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Elise/Spells/EliseSpiderQAbility/EliseSpiderQCast', 'q')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Elise/Spells/EliseSpiderWAbility/EliseSpiderW', 'w')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Elise/Spells/EliseSpiderEAbility/EliseSpiderE', 'e')

        if num_id == 76: # Nidalee
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Nidalee/Spells/Takedown', 'q')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Nidalee/Spells/Pounce', 'w')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Nidalee/Spells/Swipe', 'e')

        if num_id == 126: # Jayce
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Jayce/Spells/JayceShockBlastAbility/JayceShockBlast', 'q')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Jayce/Spells/JayceHyperChargeAbility/JayceHyperCharge', 'w')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Jayce/Spells/JayceAccelerationGateAbility/JayceAccelerationGate', 'e')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Jayce/Spells/JayceStanceHtGAbility/JayceStanceGtH', 'r')

        if num_id == 246: # Qiyana
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Qiyana/Spells/QiyanaQAbility/QiyanaQ_Water', 'q')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Qiyana/Spells/QiyanaQAbility/QiyanaQ_Rock', 'q')
            self.__get_spell(num_id, champion_data, spells_values, 'Characters/Qiyana/Spells/QiyanaQAbility/QiyanaQ_Grass', 'q')

    def __get_client_data(self, num_id):
        if not num_id in self.champions_client:
            return

        main_url = 'https://d28xe8vt774jo5.cloudfront.net/'
        current_champion = self.champions_client[num_id]
        default_skin = current_champion['skins'][0]
        abilities = current_champion['spells']

        self.output_dict[num_id]['iconImage'] = current_champion['squarePortraitPath'].lower()
        self.output_dict[num_id]['splashImage'] = default_skin['uncenteredSplashPath'].lower()
        self.output_dict[num_id]['tileImage'] = default_skin['tilePath'].lower()
        self.output_dict[num_id]['loadscreenImage'] = default_skin['loadScreenPath'].lower()

        passive_video = current_champion['passive']['abilityVideoPath']
        if passive_video:
            self.output_dict[num_id]['abilities']['p']['video'] = main_url + passive_video

        for ability in abilities:
            key = ability['spellKey'].lower()
            ability_video = ability['abilityVideoPath']
            if ability_video:
                self.output_dict[num_id]['abilities'][key]['video'] = main_url + ability_video

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


        if num_id == 60 and letter in ['q', 'w', 'e']: # Elise
            spell_desc_main = self.__get_string(desc_tooltip)
        
        if num_id == 76 and letter in ['q', 'w', 'e']: # Nidalee
            spell_desc_main = self.__get_string(desc_tooltip)

        if num_id == 126 and letter in ['q', 'w', 'e', 'r']: # Jayce
            spell_desc_main = self.__get_string(desc_tooltip) 


        if desc_tooltip_below_line:
            spell_desc_main += '<br><br>' + self.__get_string(desc_tooltip_below_line)


        spell_icons = getf(m_spell, 'mImgIconName', [])
        spell_icons = [image_to_png(icon) for icon in spell_icons]
        spell_icons = list(dict.fromkeys(spell_icons))


        spell_desc_scaling_raw = getf(m_lists, "LevelUp", {})
        spell_desc_scaling = self.__process_spell_scaling(spell_desc_scaling_raw, spell_id, spells_values, letter)


        output_spell = {
            'name': spell_name,
            #'desc': self.__desc_recursive_replace(spell_desc_main, num_id),
            'desc': self.__generate_desc(self.__desc_recursive_replace(spell_desc_main, num_id, letter), spell_id, spells_values),
            'scalings': spell_desc_scaling,
            'icons': spell_icons
        }

        generic_cooldown_key = "spell_cooldown_generic"
        desc_cooldown = getf(m_loc_keys, "keyCooldown", generic_cooldown_key)

        if desc_cooldown == generic_cooldown_key and (not getf(spells_values[spell_id], 'cooldown') or spells_values[spell_id]['cooldown'][1] == 0):
            desc_cooldown = 'spell_cooldown_nocooldown'

        spell_desc_cooldown = self.__get_string(desc_cooldown)
        if spell_desc_cooldown:
            spell_desc_cooldown = self.__desc_recursive_replace(spell_desc_cooldown, num_id, letter)
            output_spell['cooldown'] = self.__generate_desc(spell_desc_cooldown, spell_id, spells_values)


        if letter != 'p':
            generic_cost_key = "spell_default_cost"
            desc_cost = getf(m_loc_keys, "keyCost", generic_cost_key)
            spell_desc_cost = self.__get_string(desc_cost)

            if '@AbilityResourceName@' in spell_desc_cost:
                ar_type = spells_values['ar_type']
                spell_desc_cost = spell_desc_cost.replace('@AbilityResourceName@', self.__get_string(f'game_ability_resource_{RESOURCE_TYPES.get(ar_type, 14)}'))
            
            spell_desc_cost = self.__desc_recursive_replace(spell_desc_cost, num_id, letter)
            output_spell['cost'] = self.__generate_desc(spell_desc_cost, spell_id, spells_values)

        self.output_dict[num_id]['abilities'][letter]['data'].append(output_spell)

    def __process_spell_scaling(self, spell_desc_scaling_raw, spell_id, spells_values, letter):
        scaling_elements = spell_desc_scaling_raw.get("elements")
        scaling_levels = 1 + spell_desc_scaling_raw.get("levelCount", 5)
        if not scaling_elements:
            return ""
        
        return_array = []

        for element in scaling_elements:
            element_style = getf(element, 'Style')
            name_override = getf(element, 'nameOverride')
            element_type = getf(element, 'type', '').lower()


            if element_type == 'effect%damount':
                type_index = getf(element, 'typeIndex', 1)
                element_type = f'effect{type_index}amount'

            if element_type == 'ammorechargetime':
                name_override = 'spell_listtype_rechargetime'

            if element_type == 'cooldown':
                name_override = 'spell_listtype_cooldown'

            if element_type == 'castrange':
                name_override = 'spell_listtype_range'

            if element_type == 'cost':
                name_override = 'spell_listtype_cost'

            if element_type == 'basecost':
                if not name_override:
                    name_override = 'spell_listtype_cost'
                if not getf(spells_values[spell_id], element_type):
                    element_type = 'cost'
                

            current_string = '<scalingcontainer><scalingblock>' + self.__get_string(name_override) + '</scalingblock>'
            current_string = self.__desc_recursive_replace(current_string, 0, letter)

            if '@AbilityResourceName@' in current_string:
                ar_type = spells_values['ar_type']
                current_string = current_string.replace('@AbilityResourceName@', self.__get_string(f'game_ability_resource_{RESOURCE_TYPES.get(ar_type, 14)}'))


            multiplier = element.get("multiplier", 1)
            values = [str(round_number(spells_values[spell_id][element_type][i] * multiplier, 2)) for i in range(1, scaling_levels)]

            if not element_style:
                current_string += f"<scalingblock>[{'/'.join(values)}]</scalingblock>"
            elif element_style == 1:
                current_string += f"<scalingblock>[{re.sub('@NUMBER@', '/'.join(values), self.__get_string('number_formatting_percentage_format'), flags=re.IGNORECASE)}]</scalingblock>"

            return_array.append(current_string + '</scalingcontainer>')

        return ''.join(return_array)

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

            decimals = 2
            var_name = search_result.split('*')[0]
            var_mod = search_result.split('*')[1] if '*' in search_result else '1'

            if '.' in var_name:
                var_name, decimals = tuple(var_name.split('.'))
            if '|' in var_name:
                var_name, decimals = tuple(var_name.split('|'))

            if var_mod == '100%':
                var_mod = 100

            try:
                var_mod = float(var_mod)
            except:
                var_mod = 1

            replacement = getf(effects[current_spell_id], var_name)

            if replacement is None:
                return '@' + matches.group(2) + '@'
            else:
                replacement = replacement[1]

            if isinstance(replacement, (int, float)):
                replacement = round_number(float(replacement) * var_mod, int(decimals), True)

            return replacement

        desc = re.sub(r' size=\'\d+\'', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(<br>){3,}', '<br><br>', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(^(<br>)+)|((<br>)+$)', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'(<rules>|<flavortext>|<section>)(<br>)+', r'\1', desc, flags=re.IGNORECASE)
        desc = re.sub(r'@spell\.[a-z]+([QWER]):hotkey@', '\\1', desc, flags=re.IGNORECASE)
        desc = re.sub(r'@SpellModifierDescriptionAppend@', '', desc, flags=re.IGNORECASE)

        return re.sub(r'(@)(.*?)(@)', replace_callback, desc, flags=re.IGNORECASE)
    
    def __f_vars_replace(self, desc, num_id, letter):

        if num_id == 136: # Aurelion Sol
            if letter == 'w':
                desc = desc.replace('@f7.1@', '@CD@')

        if num_id == 432: # Bard
            if letter == 'p':
                desc = desc.replace('@f1@', '20')
                desc = desc.replace('@f4@', '1')
                desc = desc.replace('@f5@', '@BaseMeepSpawnCD@')
            elif letter == 'w':
                desc = desc.replace('@f2@', '@MaxPacks@')
                desc = desc.replace('@f7@', '@Ammo_Cooldown@')

        if num_id == 200: # Bel'Veth
            if letter == 'q':
                desc = desc.replace('@f1@', '@PerSideCooldown@')
            elif letter == 'e':
                desc = desc.replace('@f2.0@', '@NumberOfStrikes.0@') # '@TotalStrikes.0@')

        if num_id == 245: # Ekko
            if letter == 'p':
                desc = desc.replace('@f5@', '@effect2amount*100@')

        if num_id == 60: # Elise
            if letter == 'p':
                desc = desc.replace('@f3@', '@spell.eliser:effect5amount@')

        if num_id == 41: # Gangplank
            if letter == 'e':
                desc = desc.replace('@f5@', '@effect2amount@')

        if num_id == 86: # Garen
            if letter == 'e':
                desc = desc.replace('@f1@', '@NumTicks@')

        if num_id == 420: # Illaoi
            if letter == 'e':
                desc = desc.replace('@f1@', '@{87aff6dd}@')

        if num_id == 39: # Irelia
            if letter == 'q':
                desc = desc.replace('@f1@', '@Cooldown@')

        if num_id == 141: # Kayn
            if letter == 'e':
                desc = desc.replace('@f15@', '@Cooldown@')

        if num_id == 203: # Kindred
            if letter == 'p':
                desc = desc.replace('@f2@', '@effect1amount@')
                desc = desc.replace('@f7@', '@effect3amount@')
                desc = desc.replace('@f8@', '@effect2amount*3@')
                desc = desc.replace('@f9@', '@effect2amount@')

        if num_id == 897: # K'Sante'
            if letter == 'q':
                desc = desc.replace('@f1.2@', '@BaseCD@')

        if num_id == 4: # Twisted Fate
            if letter == 'w':
                desc = desc.replace('@ttBlueDamage@', '0')
                desc = desc.replace('@ttRedDamage@', '0')
                desc = desc.replace('@ttGoldDamage@', '0')

        if num_id == 133: # Quinn
            if letter == 'p':
                desc = desc.replace('@f1@', '@spell.quinnr:harriercooldown@')

        if num_id == 497: # Rakan
            if letter == 'e':
                desc = desc.replace('@f2@', '@effect4amount@')

        if num_id == 33: # Rammus
            if letter == 'w':
                desc_temp = self.__get_string('number_formatting_percentage_format').replace('@NUMBER@', '@BonusArmorPercent*100@')
                desc = desc.replace('@F1@',desc_temp)
                desc_temp = self.__get_string('number_formatting_percentage_format').replace('@NUMBER@', '@BonusMRPercent*100@')
                desc = desc.replace('@F2@', desc_temp)

        if num_id == 134: # Syndra
            if letter == 'w':
                desc = desc.replace('@f2@', '@SlowDuration@')

        if num_id == 45: # Veigar
            if letter == 'w':
                desc = desc.replace('@f1@', '@effect3amount@')

        if num_id == 498: # Xayah
            if letter == 'p':
                desc = desc.replace('@f14@', '@effect6amount@')
                desc = desc.replace('@f16', '@effect8amount')
                desc = desc.replace('@f12@', '@effect1amount@')

        if num_id == 157: # Yasuo
            if letter == 'q':
                desc = desc.replace('@f1@', '@Cooldown@')

        if num_id == 777: # Yone
            if letter == 'q':
                desc = desc.replace('@f1@', '@Cooldown@')
            elif letter == 'w':
                desc = desc.replace('@f1@', '@Cooldown@')

        desc = re.sub(r'@f\d+[^@]{0,}@', '0', desc, flags=re.IGNORECASE)

        return desc