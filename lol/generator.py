import requests
import ujson
from lol.items import ItemsProcessor
from utils import *
    
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