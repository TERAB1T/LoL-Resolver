import requests
from concurrent.futures import ThreadPoolExecutor
import re
import redis
import ujson
from tft.units_processor import TFTUnitsProcessor
from utils import *

def get_tftmap_file(version):

    ###
    #with open(r"C:\Users\Alex\Desktop\tft-test\map22.bin.json", 'r', encoding='utf-8') as file:
    #    return ujson.load(file)
    ###

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

def get_set_items(tft_data):
    set_root = get_set_root(tft_data)
    item_ids = {}
    augment_ids = {}

    for item_list in set_root["itemLists"]:
        for item_link in tft_data[item_list]["mItems"]:
            current_item = tft_data[item_link]

            item_id = current_item.get("mName", current_item.get(hash_fnv1a("mName")))
            item_name = current_item.get("mDisplayNameTra", current_item.get(hash_fnv1a("mDisplayNameTra")))
            item_desc = current_item.get("mDescriptionNameTra", current_item.get(hash_fnv1a("mDescriptionNameTra")))
            item_icon = current_item.get("mIconPath", current_item.get(hash_fnv1a("mIconPath")))

            if item_id and item_name and item_desc and item_icon:
                if 'augments' in item_icon.lower():
                    augment_ids[item_id] = current_item
                elif not 'augment' in item_id.lower():
                    item_ids[item_id] = current_item
    
    print(f"Items: {len(item_ids)}")
    for id, item in sorted(item_ids.items()):
        print(f"  {id}")

    print(f"Augments: {len(augment_ids)}")
    for id, item in sorted(augment_ids.items()):
        aug_tags = item.get("ItemTags", item.get(hash_fnv1a("ItemTags")))

        if aug_tags:
            if '{d11fd6d5}' in aug_tags:
                print(f"  {id}  |  серебро")
            if '{ce1fd21c}' in aug_tags:
                print(f"  {id}  |  золото")
            if '{cf1fd3af}' in aug_tags:
                print(f"  {id}  |  призма")
        else:
            print(f"  {id}")

    
def generate_version(input_version, output_dir):
    print(f"TFT Units: generating version {input_version}...")
    tft_data = get_tftmap_file(input_version)
    unit_properties = filter_unit_properties(tft_data)

    #get_set_items(tft_data)
    #return

    unit_ids = get_unit_ids(tft_data)
    
    unit_list = download_all_units(input_version, unit_ids)

    languages = cd_get_languages(input_version) # ["ru_ru"]

    if not tft_data:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(input_version, lang)
        processor = TFTUnitsProcessor(input_version, output_dir, lang, tft_data, unit_list, unit_properties, strings)

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

def filter_unit_properties(tft_data):
    return_dict = {}

    for key, value in tft_data.items():
        if value.get('__type') == 'TftUnitPropertyDefinition' and value.get('name') and value.get('DefaultValue') and (value['DefaultValue'].get("__type") == "TftUnitPropertyValueInteger" or value['DefaultValue'].get("__type") == "TftUnitPropertyValueFloat"):
            return_dict[value["name"].lower()] = value["DefaultValue"].get("value", 0)

    return return_dict

def generate_tft_units(input_version, output_dir, cache = False):
    redis_cache = {}
    redis_con = None

    try:
        if cache:
            redis_con = redis.Redis(host='localhost', port=6379, decode_responses=True)
            redis_con.ping()
    except:
        redis_con = None
    
    tft_units_urls = ["data/maps/shipping/map22/map22.bin.json"]

    if redis_con and redis_con.exists("tft-units"):
        redis_cache = ujson.loads(redis_con.get("tft-units"))

    if input_version == 'all':
        versions = cd_get_versions()

        for version in versions:
            version_name = version.get('name')
            last_modified = version.get('mtime')

            if version_name not in redis_cache:
                redis_cache[version_name] = {
                    "lastModified": ''
                }

            if redis_cache[version_name]["lastModified"] != last_modified:
                generate_version(version_name, output_dir)

                if redis_con:
                    redis_cache[version_name]["lastModified"] = last_modified
                    redis_con.set("tft-units", ujson.dumps(redis_cache))
            else:
                print(f"Version {version_name} is up to date. Skipping...")
    elif re.match(r'^\d+\.\d+$', input_version):
        versions = cd_get_versions()
        version = next((element for element in versions if element['name'] == input_version), None)

        if version:
            version_name = version.get('name')
            last_modified = version.get('mtime')

            if version_name not in redis_cache:
                redis_cache[version_name] = {
                    "lastModified": ''
                }

            if redis_cache[version_name]["lastModified"] != last_modified:
                generate_version(version_name, output_dir)

                if redis_con:
                    redis_cache[version_name]["lastModified"] = last_modified
                    redis_con.set("tft-units", ujson.dumps(redis_cache))
            else:
                print(f"Version {version_name} is up to date. Skipping...")
        else:
            print(f"Version {input_version} not found.")
    elif input_version in ['latest', 'pbe']: # re.match(r'^\d+\.\d+$', input_version) or
        if input_version not in redis_cache:
            redis_cache[input_version] = {
                "status": '',
                "lastModified": ''
            }

        last_modified = get_last_modified(get_final_url(input_version, tft_units_urls))
        input_version_modified = "live" if input_version == "latest" else input_version
        response = requests.get(f"https://raw.communitydragon.org/status.{input_version_modified}.txt")

        if response.status_code == 200:
            patch_status = response.text
        else:
            return

        if redis_cache[input_version]["status"] != patch_status and "done" in patch_status:
            if redis_cache[input_version]["lastModified"] != last_modified:
                generate_version(input_version, output_dir)

                if redis_con:
                    redis_cache[input_version]["status"] = patch_status
                    redis_cache[input_version]["lastModified"] = last_modified
                    redis_con.set("tft-units", ujson.dumps(redis_cache))
            else:
                print(f"Version {input_version} is up to date. Skipping...")
        elif redis_cache[input_version]["status"] == patch_status:
            print(f"Version {input_version} is up to date. Skipping...")