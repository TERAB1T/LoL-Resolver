import re
import os
from time import time
import ujson
import requests
import redis
from xxhash import xxh64_intdigest, xxh3_64_intdigest
from constants import REDIS_PREFIX, REDIS_HOST, REDIS_PORT
import urllib3
from typing import Callable, Any, List, Dict, Optional, Union

def timer_func(func: Callable) -> Callable:
    def wrap_func(*args: Any, **kwargs: Any) -> Any:
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func

def hash_xxhash64(key: str, bits: int = 39) -> str:
    key_int = xxh64_intdigest(key.lower())
    masked_key = key_int & ((1 << bits) - 1)
    return "{" + f"{masked_key:010x}" + "}"

def hash_xxhash3(key: str, bits: int = 39) -> str:
    key_int = xxh3_64_intdigest(key.lower())
    masked_key = key_int & ((1 << bits) - 1)
    return "{" + f"{masked_key:010x}" + "}"

def hash_fnv1a(key: str) -> str:
    hash_value = 0x811c9dc5

    for char in key.lower():
        hash_value ^= ord(char)
        hash_value *= 0x01000193
        hash_value &= 0xFFFFFFFF

    return '{' + f"{hash_value:08x}" + '}'

def is_fnv1a(hash_string: str) -> bool:
    if not hash_string:
        return False
    
    return bool(re.fullmatch(r'\{[0-9a-f]{8}\}', hash_string))

def image_to_png(url: str) -> str:
    return re.sub(r'\.(tex|dds)', '.png', url, flags=re.IGNORECASE).lower()

def cd_get_languages(version: str) -> List[str]:
    url = f"https://raw.communitydragon.org/json/{version}/game/"
    http = urllib3.PoolManager()
    response = http.request("GET", url)

    if response.status == 200:
        langs_raw = ujson.loads(response.data)
        languages = [file.get('name') for file in langs_raw if file.get('type') == 'directory' and re.match(r'^[a-z]{2}_[a-z]{2}$', file.get('name'))]
        languages = [lang for lang in languages if lang not in ['ar_ae', 'id_id']]
        return languages

    url2 = f"https://raw.communitydragon.org/json/{version}/game/data/menu/"
    response2 = http.request("GET", url2)

    if response2.status == 200:
        langs_raw = ujson.loads(response2.data)
        languages = [re.search(r'(?<=_)([a-z]{2}_[a-z]{2})(?=\.(stringtable|txt)\.json)', file.get('name'), re.IGNORECASE).group(0) for file in langs_raw if file.get('name').endswith('.json')]
        languages = [lang for lang in languages if lang not in ['ar_ae', 'id_id']]
        return languages

    return []

def cd_get_versions() -> List[Dict[str, Any]]:
    url = "https://raw.communitydragon.org/json/"
    http = urllib3.PoolManager()
    response = http.request("GET", url)

    if response.status == 200:
        versions_raw = ujson.loads(response.data)
        versions = [file for file in versions_raw if re.match(r'^\d+\.\d+$', file.get('name')) and float(file.get('name').split(".")[0]) > 10]
        versions = sorted(versions, key=lambda version: float(re.sub(r'\.(\d)$', r'.0\1', version['name'])))
        return versions
    
    return []

def cd_get_versions_clean() -> List[str]:
    versions_raw = cd_get_versions()
    return [x.get('name') for x in versions_raw]

def get_last_modified(input_version: str, file_url: str) -> Optional[str]:
    file_url = f'https://raw.communitydragon.org/{input_version}/content-metadata.json'  # Temp solution! Re-write.
    http = urllib3.PoolManager()
    try:
        response = http.request("HEAD", file_url, headers={'Cache-Control': 'no-cache'})
        return response.getheader('Last-Modified')
    except Exception:
        return None

def get_final_url(version: str, urls: List[str]) -> Optional[str]:
    main_url = f"https://raw.communitydragon.org/{version}/game/"
    http = urllib3.PoolManager()
    for url in urls:
        try:
            return_url = main_url + url
            response = http.request("HEAD", return_url)
            if response.status == 200:
                return return_url
        except Exception:
            pass
    return None

def cd_get_strings_file(version: str, lang: str, game: str = 'lol') -> Optional[Dict[str, str]]:
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_temp', version, 'lang')
    temp_cache_file = f"{temp_cache_dir}/{game}_{lang}.json"

    if os.path.isfile(temp_cache_file):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)["entries"]
        except Exception:
            pass

    if game == 'tft':
        urls = [f"{lang}/data/menu/en_us/tft.stringtable.json", f"{lang}/data/menu/en_us/main.stringtable.json", f"data/menu/main_{lang}.stringtable.json", f"data/menu/fontconfig_{lang}.txt.json"]
    else:
        urls = [f"{lang}/data/menu/en_us/lol.stringtable.json", f"{lang}/data/menu/en_us/main.stringtable.json", f"data/menu/main_{lang}.stringtable.json", f"data/menu/fontconfig_{lang}.txt.json"]

    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Strings file not found: {version}:{lang}.")
        return None
    
    try:
        items_response = requests.get(final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(items_response.content)

        return ujson.loads(items_response.content)["entries"]
    except requests.RequestException as e:
        print(f"An error occurred (strings file): {e}")
        return None

def get_string(strings_array: Dict[str, str], id: str) -> str:
    if not id:
        return ''
    
    id = id.lower()

    if id in strings_array:
        return strings_array[id]

    for bits in [38, 39, 40]:
        hashed3 = hash_xxhash3(id, bits)
        if hashed3 in strings_array:
            return strings_array[hashed3]

        hashed64 = hash_xxhash64(id, bits)
        if hashed64 in strings_array:
            return strings_array[hashed64]

    if "_mod_1" in id:
        return get_string(strings_array, id.replace("_mod_1", "_mod_2"))

    return ''

def is_number(num: Union[int, float, str]) -> bool:
    if isinstance(num, (int, float)):
        return True
    
    if isinstance(num, str) and re.fullmatch(r'-?\d+(\.\d+)?', num):
        return True
        
    return False

def round_number(num: Union[int, float], decimal: int, to_string: bool = False) -> Union[int, float, str]:
    if isinstance(num, (int, float)):
        if decimal == 0:
            temp_result = int(num + 0.5)
        else:
            temp_result = round(num, decimal)
        
        temp_result = int(temp_result) if isinstance(temp_result, float) and temp_result.is_integer() else temp_result

        return str(temp_result) if to_string else temp_result
    else:
        return num

def normalize_game_version(version: str) -> float:
    if not re.match(r'^\d+\.\d+$', version):
        return version

    return round_number(float(re.sub(r'\.(\d)$', r'.0\1', version)), 2)

def getf(source_dict: Dict[str, Any], val: str, default: Any = None) -> Any:
    return source_dict.get(val, source_dict.get(hash_fnv1a(val), default))

def gen_handler(version: str, output_dir: str, languages: List[str], alias: str, urls: List[str], generate_version: Callable, cache: bool = False, atlas: bool = False) -> None:
    from img_process.atlas import AtlasProcessor

    redis_cache: Dict[str, str] = {}
    redis_con: Optional[redis.Redis] = None
    redis_key = f"{REDIS_PREFIX}:{alias.replace('-', ':')}"

    alias_fixed = alias.replace('-', ' ').title().replace('Tft', 'TFT').replace('Lol', 'LoL')

    try:
        if cache:
            redis_con = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            redis_con.ping()
    except Exception:
        redis_con = None

    if redis_con and redis_con.exists(redis_key):
        redis_cache = redis_con.hgetall(redis_key)

    if re.match(r'^\d+\.\d+$', version):
        versions = cd_get_versions()
        version_info = next((element for element in versions if element['name'] == version), None)

        if version_info:
            last_modified = version_info.get('mtime')

            if version not in redis_cache:
                redis_cache[version] = ''

            if redis_cache[version] != last_modified:
                generate_version(version, output_dir, languages)

                if redis_con:
                    redis_cache[version] = last_modified
                    redis_con.hset(redis_key, mapping=redis_cache)

                if atlas:
                    processor = AtlasProcessor()
                    processor.process_icons(version, output_dir)
            else:
                print(f"{alias_fixed}: version {version} is up to date. Skipping...")
        else:
            print(f"Version {version} not found.")
    elif version in ['latest', 'pbe']:
        if version not in redis_cache:
            redis_cache[version] = ''

        last_modified = get_last_modified(version, '')

        if not last_modified:
            print(f"{alias_fixed}: version {version} not found.")
            return

        version_modified = "live" if version == "latest" else version
        http = urllib3.PoolManager()
        response = http.request("GET", f"https://raw.communitydragon.org/status.{version_modified}.txt")

        if response.status == 200:
            patch_status = response.data.decode('utf-8')
        else:
            return

        if "done" in patch_status:
            if redis_cache[version] != last_modified:
                generate_version(version, output_dir, languages)

                if redis_con:
                    redis_cache[version] = last_modified
                    redis_con.hset(redis_key, mapping=redis_cache)
            else:
                print(f"{alias_fixed}: version {version} is up to date. Skipping...")

            if atlas:
                processor = AtlasProcessor()
                processor.process_icons(version, output_dir)
        elif "running" in patch_status:
            print(f"{alias_fixed} - version {version}: CDragon is currently being updated. Please try again later.")
        elif "error" in patch_status:
            print(f"{alias_fixed} - version {version}: The latest CDragon update failed. Please try again later.")
