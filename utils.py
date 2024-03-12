from xxhash import xxh64_intdigest
import requests
import ujson
import re

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
    urls = [f"{lang}/data/menu/en_us/main.stringtable.json", f"data/menu/main_{lang}.stringtable.json", f"data/menu/fontconfig_{lang}.txt.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Strings file not found: {version}:{lang}.")
        return
    
    try:
        items_response = requests.get(final_url)
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
    
def not_none(value, default_value):
    if value is not None and value is not False:
        return value
    else:
        return default_value

def str_ireplace(before, after, string):
    return re.sub(str(before), str(after), str(string), flags=re.IGNORECASE)

def normalize_game_version(version):
    str_version = str(version)

    if not re.match(r'^\d+\.\d+$', str_version):
        return str_version

    return round_number(float(re.sub(r'\.(\d)$', r'.0\1', str_version)), 2)