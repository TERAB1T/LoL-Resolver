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
    
def generate_version(input_version, output_dir, languages):
    print(f"LoL Items: generating version {input_version}...")
    items = get_items_file(input_version)

    if not items:
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
            processor = ItemsProcessor(input_version, output_dir, lang, items, strings)
            print(" — Done!")

def generate_lol_items(input_version, output_dir, languages, cache = False, atlas = False):
    alias = 'lol-items'
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    gen_handler(input_version, output_dir, languages, alias, urls, generate_version, cache, atlas)