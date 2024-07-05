import requests
from concurrent.futures import ThreadPoolExecutor
import ujson
from lol.items import ItemsProcessor
from utils import *

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
    
def get_items_file(version):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/items.bin.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)
        except Exception as e:
            pass

    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Items file not found: {version}.")
        return
    
    try:
        items_response = requests.get(final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(items_response.content)

        return ujson.loads(items_response.content)
    except requests.RequestException as e:
        print(f"An error occurred (item file): {e}")
        return
    
def get_mode_items(map_key, current_map):
    map_root_path = modes[map_key]['path']
    map_root = getf(current_map, map_root_path, {})
    item_lists = getf(map_root, "itemLists", [])

    items = []

    for item_list_id in item_lists:
        item_list_root = getf(current_map, item_list_id, {})
        item_list = getf(item_list_root, "mItems", [])
        items = items + item_list

    return list(set(items))
    
def generate_version_items(input_version, output_dir, languages):
    print(f"LoL Items: generating version {input_version}...")

    maps = get_all_maps(input_version)
    items = get_items_file(input_version)

    if not items:
        return
    
    item_list_with_modes = {}

    for map_key in maps.keys():
        current_map = maps[map_key]

        if not current_map:
            continue

        mode_items = get_mode_items(map_key, current_map)

        for item in mode_items:
            if item not in item_list_with_modes:
                item_list_with_modes[item] = []

            item_list_with_modes[item].append(map_key)
    
    items_filtered = {}

    for item_key, item_data in items.items():
        item_id = getf(item_data, "itemID")

        if not item_id:
            continue

        if re.match(r'^\{[0-9a-f]{8}\}$', item_key):
            if hash_fnv1a(f'Items/{str(item_id)}') == item_key:
                item_key = f'Items/{str(item_id)}'

        item_modes = getf(item_list_with_modes, item_key)

        if item_modes:
            item_data['lr_modes'] = item_modes
            items_filtered[item_id] = item_data
    
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
            processor = ItemsProcessor(input_version, output_dir, lang, items_filtered, strings)
            print(" — Done!")

def generate_lol_items(input_version, output_dir, languages, cache = False, atlas = False):
    alias = 'lol-items'
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_items, cache, atlas)