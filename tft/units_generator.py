import requests
import re
import redis
import json
import os
from tft.units_processor import TFTUnitsProcessor
from utils import *

def get_tftmap_file(version):
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
    languages = cd_get_languages(inputVersion)

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(inputVersion, lang)
        processor = TFTUnitsProcessor(inputVersion, output_dir, lang, tft_data, strings)

def generate_tft_units(input_version, output_dir, cache = False):
    generate_version(input_version, output_dir) # temp