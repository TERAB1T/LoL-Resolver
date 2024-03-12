import requests
from concurrent.futures import ThreadPoolExecutor
import re
import ujson
from tft.units import TFTUnitsProcessor
from tft.items import TFTItemsProcessor
from utils import *

### COMMON ###

def get_tftmap_file(version):
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"TFT data file not found: {version}.")
        return
    
    try:
        tftmap_response = requests.get(final_url)
        return ujson.loads(tftmap_response.content)
    except requests.RequestException as e:
        print(f"An error occurred (TFT data file): {e}")
        return
    
def get_set_root(tft_data):
    tft_data_main = tft_data["{9fcfd7a6}"]
    current_set_id = tft_data_main.get("{0d43af66}", tft_data_main.get("{2caa347b}", tft_data_main.get("mDefaultSetData")))
    return tft_data[current_set_id]

def filter_unit_props(tft_data):
    unit_props = {}

    for key, value in tft_data.items():
        if value.get('__type') == 'TftUnitPropertyDefinition' and value.get('name') and value.get('DefaultValue') and (value['DefaultValue'].get("__type") == "TftUnitPropertyValueInteger" or value['DefaultValue'].get("__type") == "TftUnitPropertyValueFloat"):
            unit_props[value["name"].lower()] = value["DefaultValue"].get("value", 0)

    return unit_props


### UNITS ###
    
def generate_version_units(input_version, output_dir):
    print(f"TFT Units: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    unit_props = filter_unit_props(tft_data)
    unit_ids = get_unit_ids(tft_data)
    unit_list = download_all_units(input_version, unit_ids)

    languages = cd_get_languages(input_version) # ["ru_ru"]

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(input_version, lang)
        processor = TFTUnitsProcessor(input_version, output_dir, lang, tft_data, unit_list, unit_props, strings)

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
    unit_url = f"https://raw.communitydragon.org/{input_version}/game/{unit_id.lower()}.cdtb.bin.json"

    if re.match(r'^\d+\.\d+$', str(input_version)) and normalize_game_version(input_version) < 14.2:
        unit_url = f"https://raw.communitydragon.org/{input_version}/game/data/{unit_id.lower()}/{unit_id.split('/')[1].lower()}.bin.json"

    response = requests.get(unit_url)
    return (unit_id, ujson.loads(response.content))

def generate_tft_units(input_version, output_dir, cache = False):
    alias = 'tft-units'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, alias, urls, generate_version_units, cache)


### ITEMS / AUGMENTS ###
    
def generate_version_items(input_version, output_dir):
    print(f"TFT Items: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    unit_props = filter_unit_props(tft_data)
    items = get_set_items(tft_data)
    languages = cd_get_languages(input_version) # ["ru_ru"]

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(input_version, lang)
        processor = TFTItemsProcessor(input_version, output_dir, lang, tft_data, items, "items", unit_props, strings)

def generate_version_augments(input_version, output_dir):
    print(f"TFT Augments: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    unit_props = filter_unit_props(tft_data)
    items = get_set_items(tft_data)
    languages = ["ru_ru"] # cd_get_languages(input_version)

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(input_version, lang)
        processor = TFTItemsProcessor(input_version, output_dir, lang, tft_data, items, "augments", unit_props, strings)

def get_set_items(tft_data):
    set_root = get_set_root(tft_data)
    items = {
        'items': {},
        'augments': {}
    }

    for item_list in set_root["itemLists"]:
        for item_link in tft_data[item_list]["mItems"]:
            current_item = tft_data[item_link]

            item_id = current_item.get("mName", current_item.get(hash_fnv1a("mName")))
            item_name = current_item.get("mDisplayNameTra", current_item.get(hash_fnv1a("mDisplayNameTra")))
            item_desc = current_item.get("mDescriptionNameTra", current_item.get(hash_fnv1a("mDescriptionNameTra")))
            item_icon = current_item.get("mIconPath", current_item.get(hash_fnv1a("mIconPath")))

            if item_id and item_name and item_desc and item_icon and not 'debug' in item_id.lower():
                if 'augment' in item_id.lower():
                    items['augments'][item_id] = current_item
                else:
                    items['items'][item_id] = current_item

    return items

def generate_tft_items(input_version, output_dir, cache = False):
    alias = 'tft-items'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, alias, urls, generate_version_items, cache)

def generate_tft_augments(input_version, output_dir, cache = False):
    alias = 'tft-augments'
    urls = ["data/maps/shipping/map22/map22.bin.json"]
    gen_handler(input_version, output_dir, alias, urls, generate_version_augments, cache)