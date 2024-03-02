import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Thread,local
import re
import redis
import json
import os
from tft.units_processor import TFTUnitsProcessor
from utils import *

def get_tftmap_file(version):

    ###
    #with open(r"C:\Users\Alex\Desktop\tft-test\map22.bin.json", 'r', encoding='utf-8') as file:
    #    return json.load(file)
    ###

    urls = ["data/maps/shipping/map22/map22.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"TFT data file not found: {version}.")
        return
    
    try:
        tftmap_response = requests.get(final_url)
        return tftmap_response.json()
    except requests.RequestException as e:
        print(f"An error occurred (TFT data file): {e}")
        return
    
def generate_version(inputVersion, output_dir):
    print(f"Generating version {inputVersion}...")
    tft_data = get_tftmap_file(inputVersion)
    unit_properties = filter_unit_properties(tft_data)

    champion_list_ids = get_champion_list(tft_data)
    champion_list = download_all_champions(champion_list_ids)

    ###
    #with open(r"C:\Users\Alex\Desktop\tft-test\main.stringtable.json", 'r', encoding='utf-8') as file:
    #    strings = json.load(file)["entries"]
    #    processor = TFTUnitsProcessor(inputVersion, output_dir, "ru_ru", tft_data, strings)
    #return
    ###

    languages = cd_get_languages(inputVersion) # ["en_us", "ru_ru"]

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(inputVersion, lang)
        processor = TFTUnitsProcessor(inputVersion, output_dir, lang, tft_data, champion_list, unit_properties, strings)

def get_champion_list(tft_data):
    current_set_id = tft_data["{9fcfd7a6}"]["{0d43af66}"]
    champion_list_id = tft_data[current_set_id]["tftCharacterLists"][0]
    return tft_data[champion_list_id]['characters']

def download_all_champions(ids):
    with ThreadPoolExecutor() as executor:
        return dict(executor.map(download_champion, ids))

def download_champion(id):
    response = requests.get(f'https://raw.communitydragon.org/latest/game/{id.lower()}.cdtb.bin.json')
    return (id, response.json())

def generate_tft_units(input_version, output_dir, cache = False):
    generate_version(input_version, output_dir) # temp

def filter_unit_properties(tft_data):
    return_dict = {}

    for key, value in tft_data.items():
        if value.get('__type') == 'TftUnitPropertyDefinition' and value.get('name') and value.get('DefaultValue') and (value['DefaultValue'].get("__type") == "TftUnitPropertyValueInteger" or value['DefaultValue'].get("__type") == "TftUnitPropertyValueFloat"):
            return_dict[value["name"].lower()] = value["DefaultValue"].get("value", 0)

    return return_dict