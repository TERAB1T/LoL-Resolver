import requests
from concurrent.futures import ThreadPoolExecutor
import ujson
from lol.items import ItemsProcessor
from lol.rgm_augments import RGMAugmentsProcessor
from utils import *

### COMMON ###

modes = {
    'SR': {
        'id': 11,
        'path': 'Maps/Shipping/Map11/Modes/CLASSIC'
    },
    'ARAM': {
        'id': 12,
        'path': 'Maps/Shipping/Map12/Modes/ARAM'
    },
    'NB': {
        'id': 21,
        'path': 'Maps/Shipping/Map21/Modes/NEXUSBLITZ'
    },
    'Arena': {
        'id': 30,
        'path': 'Maps/Shipping/Map30/Modes/CHERRY'
    },
    'Swarm': {
        'id': 33,
        'path': 'Maps/Shipping/Map33/Modes/STRAWBERRY'
    }
}

def get_all_maps(input_version):
    mode_list = list(modes)
    with ThreadPoolExecutor() as executor:
        return dict(executor.map(download_map, [input_version] * len(mode_list), mode_list))

def download_map(version, map_key):
    map_id = modes[map_key]['id']

    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/map{map_id}.bin.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return (map_key, ujson.load(f))
        except Exception as e:
            pass
    
    map_url = f"https://raw.communitydragon.org/{version}/game/data/maps/shipping/map{map_id}/map{map_id}.bin.json"

    response = requests.get(map_url)
    if response.status_code == 200:
        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(response.content)

        return (map_key, ujson.loads(response.content))
    else:
        return (map_key, {})

### ITEMS ###
    
def generate_version_items(input_version, output_dir, languages):
    print(f"LoL Items: generating version {input_version}...")

    maps = get_all_maps(input_version)
    
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
            processor = ItemsProcessor(input_version, output_dir, lang, maps, modes, strings)
            print(" — Done!")

def generate_lol_items(input_version, output_dir, languages, cache = False, atlas = False):
    alias = 'lol-items'
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_items, cache, atlas)

### ARENA AUGMENTS ###
    
def generate_version_arena_augments(input_version, output_dir, languages):
    print(f"Arena Augments: generating version {input_version}...")
    arena_data = download_map(input_version, 'Arena')[1]
    if not arena_data:
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
            processor = RGMAugmentsProcessor(input_version, output_dir, 'arena', lang, arena_data, strings)
            print(" — Done!")

def generate_arena_augments(input_version, output_dir, languages, cache = False):
    alias = 'arena-augments'
    urls = ["data/maps/shipping/map30/map30.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_arena_augments, cache)

def generate_version_swarm_augments(input_version, output_dir, languages):
    print(f"Swarm Augments: generating version {input_version}...")
    swarm_data = download_map(input_version, 'Swarm')[1]
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
            processor = RGMAugmentsProcessor(input_version, output_dir, 'swarm', lang, swarm_data, strings)
            print(" — Done!")

def generate_swarm_augments(input_version, output_dir, languages, cache = False):
    alias = 'swarm-augments'
    urls = ["data/maps/shipping/map33/map33.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_swarm_augments, cache)