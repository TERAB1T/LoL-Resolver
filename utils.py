from xxhash import xxh64_intdigest
import requests
import ujson
import re
import os
import redis

def hash_xxhash(key, bits=39):
    key_int = xxh64_intdigest(key.lower())
    masked_key = key_int & ((1 << bits) - 1)
    return "{" + f"{masked_key:010x}" + "}"

def hash_fnv1a(key):
    hash_value = 0x811c9dc5

    if len(key) > 0:
        key = key.lower()
        for char in key:
            hash_value ^= ord(char)
            hash_value *= 0x01000193
            hash_value &= 0xFFFFFFFF

    return '{' + f"{hash_value:08x}" + '}'

def image_to_png(url):
    return re.sub(r'\.(tex|dds)', '.png', url, flags=re.IGNORECASE)

def cd_get_languages(version):
    url = f"https://raw.communitydragon.org/json/{version}/game/"
    response = requests.get(url)

    if response.status_code == 200:
        langs_raw = ujson.loads(response.content)
        languages = [file.get('name') for file in langs_raw if file.get('type') == 'directory' and re.match(r'^[a-z]{2}_[a-z]{2}$', file.get('name'))]
        if len(languages) != 0:
            if 'ar_ae' in languages:
                languages.remove('ar_ae')
            return languages

    url2 = f"https://raw.communitydragon.org/json/{version}/game/data/menu/"
    response2 = requests.get(url2)

    if response2.status_code == 200:
        langs_raw = ujson.loads(response2.content)
        languages = [re.search(r'(?<=_)([a-z]{2}_[a-z]{2})(?=\.(stringtable|txt)\.json)', file.get('name'), re.IGNORECASE).group(0) for file in langs_raw if file.get('name').endswith('.json')]
        if 'ar_ae' in languages:
            languages.remove('ar_ae')
        return languages
    
def cd_get_versions():
    url = "https://raw.communitydragon.org/json/"
    response = requests.get(url)

    if response.status_code == 200:
        versions_raw = ujson.loads(response.content)
        versions = [file for file in versions_raw if re.match(r'^\d+\.\d+$', file.get('name')) and float(file.get('name').split(".")[0]) > 10]
        versions = sorted(versions, key = lambda version: float(re.sub(r'\.(\d)$', r'.0\1', version['name'])))
        return versions
    
def cd_get_versions_clean():
    versions_raw = cd_get_versions()
    return list(map(lambda x: x.get('name'), versions_raw))

def get_last_modified(file_url):
    try:
        response = requests.head(file_url)
        return response.headers.get('Last-Modified')
    except requests.RequestException as e:
        raise ValueError(f"An error occurred: {e}")

def get_final_url(version, urls):
    main_url = f"https://raw.communitydragon.org/{version}/game/"
    for url in urls:
        try:
            return_url = main_url + url
            response = requests.head(return_url)
            if response.status_code == 200:
                return return_url
        except requests.RequestException:
            pass
    return None

def cd_get_strings_file(version, lang):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_temp', version, 'lang')
    temp_cache_file = f"{temp_cache_dir}/{lang}.json"

    if (os.path.isfile(temp_cache_file)):
        try:
            with open(temp_cache_file, encoding='utf-8') as f:
                return ujson.load(f)["entries"]
        except Exception as e:
            pass

    urls = [f"{lang}/data/menu/en_us/main.stringtable.json", f"data/menu/main_{lang}.stringtable.json", f"data/menu/fontconfig_{lang}.txt.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Strings file not found: {version}:{lang}.")
        return
    
    try:
        items_response = requests.get(final_url)

        os.makedirs(temp_cache_dir, exist_ok=True)
        with open(temp_cache_file, 'wb') as output_file:
            output_file.write(items_response.content)

        return ujson.loads(items_response.content)["entries"]
    except requests.RequestException as e:
        print(f"An error occurred (strings file): {e}")
        return

def get_string(strings_array, id):
    id = id.lower()

    if id in strings_array:
        return strings_array[id]

    hashed_39 = hash_xxhash(id, 39)
    hashed_40 = hash_xxhash(id, 40)

    if hashed_39 in strings_array:
        return strings_array[hashed_39]

    if hashed_40 in strings_array:
        return strings_array[hashed_40]

    if "_mod_1" in id:
        return get_string(strings_array, id.replace("_mod_1", "_mod_2"))

    return ''

def round_number(num, decimal, to_string=False):
    if isinstance(num, (int, float)):
        if decimal == 0:
            temp_result = int(num + 0.5)
        else:
            temp_result = round(num, decimal)
        
        temp_result = int(temp_result) if isinstance(temp_result, float) and temp_result.is_integer() else temp_result

        
        if to_string is True:
            return str(temp_result)
        else:
            return temp_result
    else:
        return num

def str_ireplace(before, after, string):
    return re.sub(str(before), str(after), str(string), flags=re.IGNORECASE)

def normalize_game_version(version):
    str_version = str(version)

    if not re.match(r'^\d+\.\d+$', str_version):
        return str_version

    return round_number(float(re.sub(r'\.(\d)$', r'.0\1', str_version)), 2)

def getf(dict, val, default=None):
    return dict.get(val, dict.get(hash_fnv1a(val), default))

def gen_handler(input_version, output_dir, languages, alias, urls, generate_version, cache = False, atlas = False):
    from lol.atlas import AtlasProcessor

    redis_cache = {}
    redis_con = None

    try:
        if cache:
            redis_con = redis.Redis(host='localhost', port=6379, decode_responses=True)
            redis_con.ping()
    except:
        redis_con = None

    if redis_con and redis_con.exists(alias):
        redis_cache = ujson.loads(redis_con.get(alias))

    if re.match(r'^\d+\.\d+$', input_version):
        versions = cd_get_versions()
        version = next((element for element in versions if element['name'] == input_version), None)

        if version:
            version_name = version.get('name')
            last_modified = version.get('mtime')

            if not version_name in redis_cache or not 'last_modified' in redis_cache[version_name]:
                redis_cache[version_name] = {
                    "last_modified": ''
                }

            if redis_cache[version_name]["last_modified"] != last_modified:
                generate_version(version_name, output_dir, languages)

                if redis_con:
                    redis_cache[version_name]["last_modified"] = last_modified
                    redis_con.set(alias, ujson.dumps(redis_cache))

                if atlas:
                    processor = AtlasProcessor()
                    processor.process_icons(version_name, output_dir)
            else:
                print(f"Version {version_name} is up to date. Skipping...")
        else:
            print(f"Version {input_version} not found.")
    elif input_version in ['latest', 'pbe']:
        if not input_version in redis_cache or not 'status' in redis_cache[input_version] or not 'last_modified' in redis_cache[input_version]:
            redis_cache[input_version] = {
                "status": '',
                "last_modified": ''
            }

        last_modified = get_last_modified(get_final_url(input_version, urls))
        input_version_modified = "live" if input_version == "latest" else input_version
        response = requests.get(f"https://raw.communitydragon.org/status.{input_version_modified}.txt")

        if response.status_code == 200:
            patch_status = response.text
        else:
            return

        if redis_cache[input_version]["status"] != patch_status and "done" in patch_status:
            if redis_cache[input_version]["last_modified"] != last_modified:
                generate_version(input_version, output_dir, languages)

                if redis_con:
                    redis_cache[input_version]["status"] = patch_status
                    redis_cache[input_version]["last_modified"] = last_modified
                    redis_con.set(alias, ujson.dumps(redis_cache))
            else:
                print(f"Version {input_version} is up to date. Skipping...")

            if atlas:
                processor = AtlasProcessor()
                processor.process_icons(input_version, output_dir)
        elif redis_cache[input_version]["status"] == patch_status:
            print(f"Version {input_version} is up to date. Skipping...")