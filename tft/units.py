import os
import re
import ujson
from utils import *
from stats import *
from bin_defs.bin_main import BinDefinitions

class TFTUnitsProcessor:
    def __init__(self, version, output_dir, lang, tft_data, unit_list, unit_properties, strings):
        self.version = version
        self.lang = lang
        self.strings_raw = strings

        self.hp_coef = [0.7, 1, 1.8, 3.24, 5.832]
        self.ad_coef = [0.5, 1, 1.5, 2.25, 3.375]
        if re.match(r'^\d+\.\d+$', str(version)) and normalize_game_version(version) < 12.14:
            self.ad_coef = self.hp_coef

        self.output_dict = {}
        self.output_dir = os.path.join(output_dir, f"tft-units/{version}")
        self.output_filepath = f"{self.output_dir}/{lang}.json"

        self.tft_data = tft_data
        self.unit_list = unit_list
        self.unit_properties = unit_properties

        for key, value in self.unit_list.items():
            self.__get_unit(key, value)

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

    def __desc_recursive_replace(self, desc):
        def replace_callback(matches):
            key = matches[1].strip().lower()
            str = self.__get_string(key)
            return self.__desc_recursive_replace(str)
        
        return re.sub(r'{{\s*(.*?)\s*}}', replace_callback, desc, flags=re.IGNORECASE)
    
    def __get_unit(self, unit_id, unit_data):
        #if unit_id != 'Characters/TFT13_Elise':
        #    return

        #print(unit_id)
        
        unit_id_trimmed = unit_id.split("/")[1].lower()

        root_record_path = f'{unit_id}/CharacterRecords/Root'
        root_record = getf(unit_data, root_record_path)
        if not root_record:
            return
        
        spell_names = getf(root_record, "spellNames")
        if not spell_names:
            return
        
        m_shop_data = getf(root_record, "mShopData")
        
        if not m_shop_data:
            return
        
        unit_shop_data = getf(self.tft_data, m_shop_data)

        unit_stats = {
            0:  [100.0] * 5, # ability power
            1:  [round(getf(root_record, 'baseArmor', 0), 5)] * 5, # armor
            2:  [round(getf(root_record, 'baseDamage', 0) * self.ad_coef[i], 5) for i in range(5)], # attack damage
            3:  [round(getf(root_record, 'attackSpeed', 0), 5)] * 5, # attack speed
            5:  [round(getf(root_record, 'baseSpellBlock', 0), 5)] * 5, # magic resistance
            6:  [round(getf(root_record, 'baseMoveSpeed', 0), 5)] * 5, # move speed
            7:  [round(getf(root_record, 'baseCritChance', 0), 5)] * 5, # crit chance
            8:  [round(getf(root_record, 'critDamageMultiplier', 0), 5)] * 5, # crit damage
            11: [round(getf(root_record, 'baseHP', 0) * self.hp_coef[i], 5) for i in range(5)], # max health
            28: [round(getf(root_record, 'attackRange', 0), 5)] * 5, # attack range
            33: [1] * 5, # dodge chance
        }

        self.output_dict[unit_id_trimmed] = {
            'id': unit_id.split("/")[1],
            'name': self.__get_string(getf(unit_shop_data, "mDisplayNameTra")),
            'cost': getf(root_record, 'tier', 0),
            'traits': []
        }

        if getf(unit_shop_data, 'TeamPlannerPortraitPath'):
            self.output_dict[unit_id_trimmed]['icon'] = image_to_png(getf(unit_shop_data, 'TeamPlannerPortraitPath').lower())
        elif getf(root_record, 'PortraitIcon'):
            self.output_dict[unit_id_trimmed]['icon'] = image_to_png(getf(root_record, 'PortraitIcon').lower())

        if getf(unit_shop_data, 'PcSplashPath'):
            self.output_dict[unit_id_trimmed]['splashSmall'] = image_to_png(getf(unit_shop_data, 'PcSplashPath').lower())
        elif getf(unit_shop_data, 'mIconPath'):
            self.output_dict[unit_id_trimmed]['splashSmall'] = image_to_png(getf(unit_shop_data, 'mIconPath').lower())

        if getf(unit_shop_data, 'SquareSplashPath'):
            self.output_dict[unit_id_trimmed]['splashLarge'] = image_to_png(getf(unit_shop_data, 'SquareSplashPath').lower())
        elif getf(unit_shop_data, 'mMobileIconPath'):
            self.output_dict[unit_id_trimmed]['splashLarge'] = image_to_png(getf(unit_shop_data, 'mMobileIconPath').lower())

        if getf(root_record, 'CharacterRole'):
            character_role = getf(root_record, 'CharacterRole')
            character_role_block = getf(self.tft_data, character_role, {})
            character_role_name = getf(character_role_block, 'CharacterRoleNameTra')

            if character_role_name:
                self.output_dict[unit_id_trimmed]['role'] = self.__get_string(character_role_name)

        self.output_dict[unit_id_trimmed]['stats'] = {
            'health': round_number(unit_stats[11][1], 2),
            'startingMana': round_number(getf(root_record, 'mInitialMana', 0), 2),
            'maxMana': round_number(getf(getf(root_record, "primaryAbilityResource", {}), "arBase", 100), 2),
            'attackDamage': round_number(unit_stats[2][1], 2),
            'abilityPower': round_number(unit_stats[0][1], 2),
            'armor': round_number(unit_stats[1][1], 2),
            'magicResist': round_number(unit_stats[5][1], 2),
            'attackSpeed': round_number(unit_stats[3][1], 2),
            'range': int(unit_stats[28][1] / 180)
        }

        m_linked_traits = getf(root_record, 'mLinkedTraits', [])
        for trait in m_linked_traits:
            trait_link = getf(trait, "TraitData")
            trait_data = getf(self.tft_data, trait_link, {})
            trait_id = getf(trait_data, "mName")

            if trait_id:
                self.output_dict[unit_id_trimmed]['traits'].append(trait_id.lower())

        self.output_dict[unit_id_trimmed]['abilities'] = []

        for spell_name in spell_names:
            if spell_name != 'BaseSpell' and spell_name != '':
                spell_record_path = f'{unit_id}/Spells/{spell_name}'
                self.__get_spell(unit_id_trimmed, unit_data, spell_record_path, unit_stats)

                if unit_id == 'Characters/TFT13_Jayce':
                    spell_record_path = '{113c9b5d}'
                    self.__get_spell(unit_id_trimmed, unit_data, spell_record_path, unit_stats)
                if unit_id == 'Characters/TFT13_Gangplank':
                    spell_record_path = '{63408f43}'
                    self.__get_spell(unit_id_trimmed, unit_data, spell_record_path, unit_stats)
                if unit_id == 'Characters/TFT13_Swain':
                    spell_record_path = '{f06a42c9}'
                    self.__get_spell(unit_id_trimmed, unit_data, spell_record_path, unit_stats)
                if unit_id == 'Characters/TFT13_Elise':
                    spell_record_path = '{c00bdaf9}'
                    self.__get_spell(unit_id_trimmed, unit_data, spell_record_path, unit_stats)

        if getf(unit_shop_data, 'AbilityIconPath'):
            self.output_dict[unit_id_trimmed]['abilityIcon'] = image_to_png(getf(unit_shop_data, 'AbilityIconPath').lower())
        elif getf(unit_shop_data, 'mPortraitIconPath'):
            self.output_dict[unit_id_trimmed]['abilityIcon'] = image_to_png(getf(unit_shop_data, 'mPortraitIconPath').lower())

    def __get_spell(self, unit_id_trimmed, unit_data, spell_record_path, unit_stats):
        spell_record = getf(unit_data, spell_record_path, {})
        
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
        spell_desc_main = self.__get_string(getf(m_loc_keys, "keyTooltip"))
        spell_desc_main = self.__desc_recursive_replace(spell_desc_main)

        if 'TFT10_Headliner_TRA@' in spell_desc_main:
            headliner_id = f'tft10_headliner_{unit_id_trimmed}'
            spell_desc_main = re.sub(r'@TFTUnitProperty\.[a-z]*:TFT10_Headliner_TRA@', self.__get_string(headliner_id), spell_desc_main, flags=re.IGNORECASE)

        spell_desc_scaling_raw = getf(m_lists, "LevelUp", {})
        scaling_levels = 1 + getf(spell_desc_scaling_raw, "levelCount", 3)

        var_values = {}

        for data_value in m_data_values:
            m_name = getf(data_value, "mName")
            m_values = getf(data_value, "mValues")

            if m_name and m_values:
                var_values[m_name.lower()] = [round(m_values[i], 5) for i in range(5)]
                var_values[hash_fnv1a(m_name.lower())] = var_values[m_name.lower()]

        spell_calc = {}
        spell_style = {}

        for key, value in var_values.items():
            spell_calc[key.lower()] = self.__process_value_array([value[i] for i in range(1, scaling_levels)])

        spell_calc.update(self.unit_properties)

        if m_spell_calc:
            for spell_calc_key, spell_calc_value in m_spell_calc.items():
                spell_calc[spell_calc_key.lower()] = []

                for i in range(1, scaling_levels):
                    current_var_values = {key: value[i] for key, value in var_values.items()}
                    current_unit_stats = {key: value[i] for key, value in unit_stats.items()}

                    bin_definitions = BinDefinitions(self.strings_raw, current_var_values, m_spell_calc, current_unit_stats, 'float')
                    parsed_bin = bin_definitions.calc_values(spell_calc_value)

                    if isinstance(parsed_bin, dict):
                        calculated_value = parsed_bin['value']

                        if re.match(r'^\d+\.\d+$', str(self.version)) and normalize_game_version(self.version) < 13.12:
                            spell_style[spell_calc_key.lower()] = {
                                'tag': parsed_bin['tag'],
                                'icon': parsed_bin['icon']
                            }
                    else:
                        calculated_value = parsed_bin

                    m_precision = getf(spell_calc_value, "mPrecision")

                    if not isinstance(calculated_value, (int, float)) and '%' in calculated_value:
                        spell_calc[spell_calc_key.lower()].append(calculated_value)
                    elif m_precision:
                        spell_calc[spell_calc_key.lower()].append(f"{calculated_value}|{m_precision}")
                    else:
                        spell_calc[spell_calc_key.lower()].append(float(calculated_value))

                spell_calc[spell_calc_key.lower()] = self.__process_value_array(spell_calc[spell_calc_key.lower()])
                spell_calc[hash_fnv1a(spell_calc_key.lower())] = spell_calc[spell_calc_key.lower()]

                if spell_calc_key.lower() in spell_style:
                    spell_style[hash_fnv1a(spell_calc_key.lower())] = spell_style[spell_calc_key.lower()]

        spell_desc_scaling = self.__process_spell_scaling(spell_desc_scaling_raw, var_values)

        self.output_dict[unit_id_trimmed]['abilities'].append({
            'name': spell_name,
            'desc': self.__generate_unit_tooltip(f"{spell_desc_main}{spell_desc_scaling}", spell_calc, var_values, spell_style)
        })
    
    def __process_spell_scaling(self, spell_desc_scaling_raw, var_values):
        scaling_elements = spell_desc_scaling_raw.get("elements")
        scaling_levels = 1 + spell_desc_scaling_raw.get("levelCount", 3)
        if not scaling_elements:
            return ""
        
        return_array = []

        for element in scaling_elements:
            style = element.get("Style")
            current_string = '<scalingcontainer><scalingblock>' + self.__get_string(element["nameOverride"]) + '</scalingblock>'

            if not style:
                values = [str(round_number(var_values[element["type"].lower()][i], 2)) for i in range(1, scaling_levels)]
                current_string += f"<scalingblock>[{'/'.join(values)}]</scalingblock>"
            elif style == 1:
                multiplier = element.get("multiplier", 1)
                values = [str(round_number(var_values[element["type"].lower()][i] * multiplier, 2)) for i in range(1, scaling_levels)]
                current_string += f"<scalingblock>[{str_ireplace('@NUMBER@', '/'.join(values), self.__get_string('number_formatting_percentage_format'))}]</scalingblock>"

            return_array.append(current_string + '</scalingcontainer>')

        return '<hr>' + ''.join(return_array)

    def __process_value_array(self, arr):
        arr = [round_number(x, 5, True) for x in arr]

        if all(x == arr[0] for x in arr):
            try:
                arr[0] = float(arr[0])
            except:
                pass

            return arr[0]
        else:
            return '/'.join(arr)
        
    def __generate_unit_tooltip(self, spell_desc_main, spell_calc, var_values, spell_style = {}):
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

            if var_name not in spell_calc and hash_fnv1a(var_name) in spell_calc:
                var_name = hash_fnv1a(var_name)

            if var_name in spell_calc:
                current_spell_calc = spell_calc[var_name]
                decimal_places = 0

                if var_name in var_values:
                    decimal_places = 2

                if isinstance(current_spell_calc, str) and '|' in current_spell_calc:
                    decimal_places = int(spell_calc[var_name].split('|')[1])
                    current_spell_calc = float(current_spell_calc.split('|')[0])

                if isinstance(current_spell_calc, (int, float)):
                    replacement = round_number(float(current_spell_calc) * var_mod, decimal_places, True)
                else:
                    if '/' in current_spell_calc and '%' not in current_spell_calc:
                        replacement = '/'.join([round_number(float(x) * var_mod, decimal_places, True) for x in current_spell_calc.split('/')])
                    elif '/' in current_spell_calc and '%' in current_spell_calc:
                        replacement = re.sub(' *%/', '/', current_spell_calc)
                    else:
                        replacement = current_spell_calc

            if var_name == 'value' and var_name not in spell_calc:
                replacement = '0'

            if var_name in spell_style:
                current_style = spell_style[var_name]
                replacement = f"<{current_style['tag']}>{replacement} %i:{current_style['icon']}%</{current_style['tag']}>"

            #print(matches.group(2), spell_calculations.get(var_name), replacement)
            return replacement
        
        if '@TFTUnitProperty.' in spell_desc_main:
            spell_desc_main = str_ireplace('@TFTUnitProperty.unit:', '@', spell_desc_main)
            spell_desc_main = str_ireplace('@TFTUnitProperty.:', '@', spell_desc_main)

        return re.sub(r'(@)(.*?)(@)', replace_callback, spell_desc_main, flags=re.IGNORECASE)