import requests
import re
import redis
import json
import os
from items.atlas_processor import AtlasProcessor
from items.items_processor import ItemsProcessor
from utils import *

def get_languages(version):
    url = f"https://raw.communitydragon.org/json/{version}/game/data/menu/"
    response = requests.get(url)

    if response.status_code == 200:
        langs_raw = response.json()
        languages = [re.search(r'(?<=_)([a-z]{2}_[a-z]{2})(?=\.(stringtable|txt)\.json)', file.get('name'), re.IGNORECASE).group(0) for file in langs_raw if file.get('name').endswith('.json')]
        if 'ar_ae' in languages:
            languages.remove('ar_ae')
        return languages
    
def get_versions():
    url = "https://raw.communitydragon.org/json/"
    response = requests.get(url)

    if response.status_code == 200:
        versions_raw = response.json()
        versions = [file for file in versions_raw if re.match(r'^\d+\.\d+$', file.get('name')) and float(file.get('name').split(".")[0]) > 10]
        versions = sorted(versions, key = lambda version: float(re.sub(r'\.(\d)$', r'.0\1', version['name'])))
        return versions
    
def generate_version(inputVersion, output_dir):
    print(f"Generating version {inputVersion}...")
    items = get_items_file(inputVersion)
    languages = get_languages(inputVersion)

    if not items:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = get_strings_file(inputVersion, lang)
        processor = ItemsProcessor(inputVersion, output_dir, lang, items, strings)

def generate_items(input_version, output_dir, cache = False, atlas = False):
    redis_cache = {}
    redis_con = None

    try:
        if cache:
            redis_con = redis.Redis(host='localhost', port=6379, decode_responses=True)
            redis_con.ping()
    except:
        redis_con = None

    item_urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]

    if redis_con and redis_con.exists("items"):
        redis_cache = json.loads(redis_con.get("items"))
        # print(redis_con.get("items"))

    if input_version == 'all':
        versions = get_versions()

        for version in versions:
            version_name = version.get('name')
            items_last_modified = version.get('mtime')

            if version_name not in redis_cache:
                redis_cache[version_name] = {
                    "itemsLastModified": ''
                }

            if redis_cache[version_name]["itemsLastModified"] != items_last_modified:
                generate_version(version_name, output_dir)

                if redis_con:
                    redis_cache[version_name]["itemsLastModified"] = items_last_modified
                    redis_con.set("items", json.dumps(redis_cache))

                if atlas:
                    processor = AtlasProcessor()
                    processor.process_icons(version_name, output_dir)
            else:
                print(f"Version {version_name} is up to date. Skipping...")

    elif input_version in ['latest', 'pbe']: # re.match(r'^\d+\.\d+$', input_version) or
        if input_version not in redis_cache:
            redis_cache[input_version] = {
                "status": '',
                "itemsLastModified": ''
            }

        items_last_modified = get_last_modified(get_final_url(input_version, item_urls))
        input_version_modified = "live" if input_version == "latest" else input_version
        response = requests.get(f"https://raw.communitydragon.org/status.{input_version_modified}.txt")

        if response.status_code == 200:
            patch_status = response.text
        else:
            return

        if redis_cache[input_version]["status"] != patch_status and "done" in patch_status:
            if redis_cache[input_version]["itemsLastModified"] != items_last_modified:
                generate_version(input_version, output_dir)

                if redis_con:
                    redis_cache[input_version]["status"] = patch_status
                    redis_cache[input_version]["itemsLastModified"] = items_last_modified
                    redis_con.set("items", json.dumps(redis_cache))
            else:
                print(f"Version {input_version} is up to date. Skipping...")

            if atlas:
                processor = AtlasProcessor()
                processor.process_icons(input_version, output_dir)
        elif redis_cache[input_version]["status"] == patch_status :
            print(f"Version {input_version} is up to date. Skipping...")