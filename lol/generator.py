from concurrent.futures import ThreadPoolExecutor
import ujson
from lol.champions import ChampionsProcessor
from lol.items import ItemsProcessor
from lol.rgm_augments import RGMAugmentsProcessor
from utils import *
import aiohttp
import asyncio

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
@timer_func
def get_all_maps(input_version):
    loop = asyncio.get_event_loop()
    mode_list = list(modes)
    tasks = [download_map(input_version, mode) for mode in mode_list]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return dict(results)

async def download_map(version, map_key):
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
    
    async with aiohttp.ClientSession() as session:
        async with session.get(map_url) as response:
            if response.status == 200:
                data = await response.read()
                os.makedirs(temp_cache_dir, exist_ok=True)
                with open(temp_cache_file, 'wb') as output_file:
                    output_file.write(data)

                return (map_key, ujson.loads(data))
            else:
                return (map_key, {})
    
### CHAMPIONS ###
@timer_func
def generate_version_champions(input_version, output_dir, languages):
    print(f"LoL Champions: generating version {input_version}...")

    champion_ids = get_champion_ids(input_version)
    champion_list = download_all_champions(input_version, champion_ids)

    champion_ids_client = get_champion_ids_client(input_version)
    champion_list_client = download_all_champions_client(input_version, champion_ids_client)
    
    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'lol')
            processor = ChampionsProcessor(input_version, output_dir, lang, champion_list, champion_list_client, strings)
            print(" — Done!")

def get_champion_ids(version):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/champions.bin.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)
        except Exception as e:
            pass

    urls = ["global/champions/champions.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Champions data file not found: {version}.")
        return

    try:
        champions_response = urllib3.request("GET", final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(champions_response.data)

        return ujson.loads(champions_response.data)
    except:
        print(f"An error occurred (champions data file)")
        return
    
def download_all_champions(input_version, champion_ids):
    loop = asyncio.get_event_loop()
    tasks = [download_champion(input_version, champion_id) for champion_id in champion_ids]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return dict(results)

async def download_champion(input_version, champion_id):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', input_version, 'champions')
    temp_cache_file = f"{temp_cache_dir}/{champion_id.split('/')[1].lower()}.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return (champion_id, ujson.load(f))
        except Exception as e:
            pass

    champion_url = f"https://raw.communitydragon.org/{input_version}/game/data/{champion_id.lower()}/{champion_id.split('/')[1].lower()}.bin.json"

    async with aiohttp.ClientSession() as session:
        async with session.get(champion_url) as response:
            if response.status == 200:
                data = await response.read()
                os.makedirs(temp_cache_dir, exist_ok=True)
                with open(temp_cache_file, 'wb') as output_file:
                    output_file.write(data)

                return (champion_id, ujson.loads(data))
            else:
                return (champion_id, {})


def get_champion_ids_client(version):
    champions_file = get_champion_file_client(version)
    champion_ids = []

    for champion in champions_file:
        current_champion = getf(champion, "id")

        if current_champion:
            champion_ids.append(current_champion)

    return champion_ids

def get_champion_file_client(version):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', version)
    temp_cache_file = f"{temp_cache_dir}/champions_client.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)
        except Exception as e:
            pass

    final_url = f"https://raw.communitydragon.org/{version}/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json"

    try:
        champions_response = urllib3.request("GET", final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(champions_response.data)

        return ujson.loads(champions_response.data)
    except:
        print(f"An error occurred (champions data file - client)")
        return
    
def download_all_champions_client(input_version, champion_ids):
    loop = asyncio.get_event_loop()
    tasks = [download_champion_client(input_version, champion_id) for champion_id in champion_ids]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return dict(results)

async def download_champion_client(input_version, champion_id):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_temp', input_version, 'champions_client')
    temp_cache_file = f"{temp_cache_dir}/{champion_id}.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return (champion_id, ujson.load(f))
        except Exception as e:
            pass

    champion_url = f"https://raw.communitydragon.org/{input_version}/plugins/rcp-be-lol-game-data/global/default/v1/champions/{champion_id}.json"

    async with aiohttp.ClientSession() as session:
        async with session.get(champion_url) as response:
            if response.status == 200:
                data = await response.read()
                os.makedirs(temp_cache_dir, exist_ok=True)
                with open(temp_cache_file, 'wb') as output_file:
                    output_file.write(data)

                return (champion_id, ujson.loads(data))
            else:
                return (champion_id, {})

def generate_lol_champions(input_version, output_dir, languages, cache = False):
    alias = 'lol-champions'
    urls = ["global/champions/champions.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_champions, cache)

### ITEMS ###

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
        items_response = urllib3.request("GET", final_url)
        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(items_response.data)
        return ujson.loads(items_response.data)
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

def populate_items(version, maps):
    items = get_items_file(version)
    output_items = {}

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
            output_items[item_id] = item_data
    
    return output_items

@timer_func 
def generate_version_items(input_version, output_dir, languages):
    print(f"LoL Items: generating version {input_version}...")

    maps = get_all_maps(input_version)
    items = populate_items(input_version, maps)
    supported_langs = cd_get_languages(input_version)
    if languages[0] == 'all':
        languages = supported_langs

    for lang in languages:
        print(f"  {lang}", end="")

        if not lang in supported_langs:
            print(f" — This language is not supported. Supported languages: {', '.join(supported_langs)}.")
            continue
        else:
            strings = cd_get_strings_file(input_version, lang, 'lol')
            processor = ItemsProcessor(input_version, output_dir, lang, items, strings)
            print(" — Done!")

def generate_lol_items(input_version, output_dir, languages, cache = False, atlas = False):
    alias = 'lol-items'
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_items, cache, atlas)

### ARENA AUGMENTS ###
    
def generate_version_arena_augments(input_version, output_dir, languages):
    print(f"Arena Augments: generating version {input_version}...")
    arena_data = asyncio.run(download_map(input_version, 'Arena'))[1]
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
            strings = cd_get_strings_file(input_version, lang, 'lol')
            processor = RGMAugmentsProcessor(input_version, output_dir, 'arena', lang, arena_data, strings)
            print(" — Done!")

def generate_arena_augments(input_version, output_dir, languages, cache = False):
    alias = 'arena-augments'
    urls = ["data/maps/shipping/map30/map30.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_arena_augments, cache)

def generate_version_swarm_augments(input_version, output_dir, languages):
    print(f"Swarm Augments: generating version {input_version}...")
    swarm_data = asyncio.run(download_map(input_version, 'Swarm'))[1]
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
            strings = cd_get_strings_file(input_version, lang, 'lol')
            processor = RGMAugmentsProcessor(input_version, output_dir, 'swarm', lang, swarm_data, strings)
            print(" — Done!")

def generate_swarm_augments(input_version, output_dir, languages, cache = False):
    alias = 'swarm-augments'
    urls = ["data/maps/shipping/map33/map33.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version_swarm_augments, cache)