import requests
from concurrent.futures import ThreadPoolExecutor
import re
import ujson
from rgm.swarm_augments import SwarmAugmentsProcessor
from utils import *

def get_swarmmap_file(version):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/map33.bin.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)
        except Exception as e:
            pass

    urls = ["data/maps/shipping/map33/map33.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Swarm data file not found: {version}.")
        return
    
    try:
        swarmmap_response = requests.get(final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(swarmmap_response.content)

        return ujson.loads(swarmmap_response.content)
    except requests.RequestException as e:
        print(f"An error occurred (Swarm data file): {e}")
        return
    
def generate_version_augments(input_version, output_dir, languages):
    print(f"Swarm Augments: generating version {input_version}...")
    swarm_data = get_swarmmap_file(input_version)
    if not swarm_data:
        return
    
    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang)
            processor = SwarmAugmentsProcessor(input_version, output_dir, lang, swarm_data, strings)
            print(" — Done!")

def generate_swarm_augments(input_version, output_dir, languages, cache = False):
    alias = 'tft-augments'
    urls = ["data/maps/shipping/map33/map33.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_augments, cache)