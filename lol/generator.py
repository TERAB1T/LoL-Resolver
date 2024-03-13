import requests
import ujson
from lol.items import ItemsProcessor
from utils import *
    
def get_items_file(version):
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Items file not found: {version}.")
        return
    
    try:
        items_response = requests.get(final_url)
        return ujson.loads(items_response.content)
    except requests.RequestException as e:
        print(f"An error occurred (item file): {e}")
        return
    
def generate_version(inputVersion, output_dir):
    print(f"LoL Items: generating version {inputVersion}...")
    items = get_items_file(inputVersion)
    languages = cd_get_languages(inputVersion)

    if not items:
        return

    for lang in languages:
        print(f"  {lang}")
        strings = cd_get_strings_file(inputVersion, lang)
        processor = ItemsProcessor(inputVersion, output_dir, lang, items, strings)

def generate_lol_items(input_version, output_dir, cache = False, atlas = False):
    alias = 'lol-items'
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    gen_handler(input_version, output_dir, alias, urls, generate_version, cache, atlas)