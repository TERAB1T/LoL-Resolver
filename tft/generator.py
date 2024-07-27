import requests
from concurrent.futures import ThreadPoolExecutor
import re
import ujson
from tft.units import TFTUnitsProcessor
from tft.traits import TFTTraitsProcessor
from tft.items import TFTItemsProcessor
from utils import *

### COMMON ###

def get_tftmap_file(version):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/map22.bin.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)
        except Exception as e:
            pass

    urls = ["data/maps/shipping/map22/map22.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"TFT data file not found: {version}.")
        return
    
    try:
        tftmap_response = requests.get(final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(tftmap_response.content)

        return ujson.loads(tftmap_response.content)
    except requests.RequestException as e:
        print(f"An error occurred (TFT data file): {e}")
        return
    
def get_set_root(tft_data):
    tft_data_main = tft_data["{9fcfd7a6}"]
    current_set_id = getf(tft_data_main, "mDefaultSetData", getf(tft_data_main, "DefaultSetData"))
    return tft_data[current_set_id]

def filter_unit_props(tft_data):
    unit_props = {}

    for key, value in tft_data.items():
        if value.get('__type') == 'TftUnitPropertyDefinition' and value.get('name') and value.get('DefaultValue') and (value['DefaultValue'].get("__type") == "TftUnitPropertyValueInteger" or value['DefaultValue'].get("__type") == "TftUnitPropertyValueFloat"):
            unit_props[value["name"].lower()] = value["DefaultValue"].get("value", 0)

    return unit_props

### UNITS ###
    
def generate_version_units(input_version, output_dir, languages):
    print(f"TFT Units: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    if not tft_data:
        return
    
    unit_props = filter_unit_props(tft_data)
    unit_ids = get_unit_ids(tft_data)
    unit_list = download_all_units(input_version, unit_ids)

    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'tft')
            processor = TFTUnitsProcessor(input_version, output_dir, lang, tft_data, unit_list, unit_props, strings)
            print(" — Done!")

def get_unit_ids(tft_data):
    set_root = get_set_root(tft_data)
    unit_ids = []

    if set_root.get("tftCharacterLists"):
        unit_list_id = set_root["tftCharacterLists"][0]
        unit_ids = tft_data[unit_list_id]['characters']
    else:
        lists = [tft_data[item]["characters"] for item in set_root["characterLists"]]
        unit_ids = max(lists, key=len)

    for i in range(len(unit_ids)):
        if re.match(r'^\{.*?\}$', unit_ids[i]):
            unit_ids[i] = f"Characters/{tft_data[unit_ids[i]]['name']}"

    return unit_ids

def download_all_units(input_version, unit_ids):
    with ThreadPoolExecutor() as executor:
        return dict(executor.map(download_unit, [input_version] * len(unit_ids), unit_ids))

def download_unit(input_version, unit_id):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', input_version, 'units')
    temp_cache_file = f"{temp_cache_dir}/{unit_id.split('/')[1].lower()}.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return (unit_id, ujson.load(f))
        except Exception as e:
            pass

    unit_url = f"https://raw.communitydragon.org/{input_version}/game/{unit_id.lower()}.cdtb.bin.json"

    if re.match(r'^\d+\.\d+$', str(input_version)) and normalize_game_version(input_version) < 14.02:
        unit_url = f"https://raw.communitydragon.org/{input_version}/game/data/{unit_id.lower()}/{unit_id.split('/')[1].lower()}.bin.json"

    response = requests.get(unit_url)
    if response.status_code == 200:
        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(response.content)

        return (unit_id, ujson.loads(response.content))
    else:
        return (unit_id, {})

def generate_tft_units(input_version, output_dir, languages, cache = False):
    alias = 'tft-units'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_units, cache)

### TRAITS ###

def generate_version_traits(input_version, output_dir, languages):
    print(f"TFT Traits: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    if not tft_data:
        return
    
    unit_props = filter_unit_props(tft_data)
    trait_units = get_trait_units(tft_data, download_all_units(input_version, get_unit_ids(tft_data)))
    trait_list = get_set_traits(tft_data)

    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'tft')
            processor = TFTTraitsProcessor(input_version, output_dir, lang, tft_data, trait_list, trait_units, unit_props, strings)
            print(" — Done!")

def get_trait_units(tft_data, unit_list):
    trait_units = {}

    for unit_id, unit_data in unit_list.items():
        unit_id_trimmed = unit_id.split("/")[1].lower()

        root_record_path = f'{unit_id}/CharacterRecords/Root'
        root_record = getf(unit_data, root_record_path)
        if not root_record:
            continue

        m_linked_traits = getf(root_record, 'mLinkedTraits')
        if not m_linked_traits:
            continue

        unit_tier = getf(root_record, 'tier', 999)

        for trait in m_linked_traits:
            trait_link = getf(trait, "TraitData")
            trait_data = getf(tft_data, trait_link, {})
            trait_id = getf(trait_data, "mName")

            if trait_id:
                trait_id = trait_id.lower()

                if trait_id not in trait_units:
                    trait_units[trait_id] = {}

                if unit_id_trimmed not in trait_units[trait_id]:
                    trait_units[trait_id][unit_id_trimmed] = unit_tier

    for trait_id, trait_data in trait_units.items():
        trait_units[trait_id] = [key for key, _ in sorted(trait_data.items(), key=lambda x: (x[1], x[0]))]

    return trait_units

def get_set_traits(tft_data):
    set_root = get_set_root(tft_data)
    traits = {}

    trait_lists = getf(set_root, "TraitLists", [getf(set_root, "traitList")])

    for trait_list in trait_lists:
        for trait_link in getf(tft_data[trait_list], "mTraits", []):
            current_trait = tft_data[trait_link]

            trait_id =   getf(current_trait, "mName")
            trait_name = getf(current_trait, "mDisplayNameTra")
            trait_desc = getf(current_trait, "mDescriptionNameTra")
            trait_icon = getf(current_trait, "mIconPath")

            if trait_id and trait_name and trait_desc and trait_icon:
                traits[trait_id] = current_trait

    return traits

def generate_tft_traits(input_version, output_dir, languages, cache = False):
    alias = 'tft-traits'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_traits, cache)

### ITEMS / AUGMENTS ###
    
def generate_version_items(input_version, output_dir, languages):
    print(f"TFT Items: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    if not tft_data:
        return
    
    unit_props = filter_unit_props(tft_data)
    items = get_set_items(tft_data)
    
    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'tft')
            processor = TFTItemsProcessor(input_version, output_dir, lang, tft_data, items, "items", unit_props, strings)
            print(" — Done!")

def generate_version_augments(input_version, output_dir, languages):
    print(f"TFT Augments: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    if not tft_data:
        return
    
    unit_props = filter_unit_props(tft_data)
    items = get_set_items(tft_data)
    
    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'tft')
            processor = TFTItemsProcessor(input_version, output_dir, lang, tft_data, items, "augments", unit_props, strings)
            print(" — Done!")

def get_set_items(tft_data):
    set_root = get_set_root(tft_data)
    items = {
        'items': {},
        'augments': {}
    }

    for item_list in set_root["itemLists"]:
        for item_link in tft_data[item_list]["mItems"]:
            current_item = tft_data[item_link]

            item_id =   getf(current_item, "mName")
            item_name = getf(current_item, "mDisplayNameTra")
            item_desc = getf(current_item, "mDescriptionNameTra")
            item_icon = getf(current_item, "mIconPath")

            if item_id and item_name and item_desc and item_icon and not 'debug' in item_id.lower() and not '_HR' in item_id and not 'empty' in item_id.lower() and not 'blankslot' in item_id.lower() and not 'admincause' in item_id.lower() and not 'tft_assist_' in item_id.lower():
                if 'augment' in item_id.lower():
                    items['augments'][item_id] = current_item
                else:
                    items['items'][item_id] = current_item

    return items

def generate_tft_items(input_version, output_dir, languages, cache = False):
    alias = 'tft-items'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_items, cache)

def generate_tft_augments(input_version, output_dir, languages, cache = False):
    alias = 'tft-augments'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_augments, cache)