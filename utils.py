from xxhash import xxh64_intdigest
import requests
import sys
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

def get_items_file(version):
    urls = ["items.cdtb.bin.json", "global/items/items.bin.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Items file not found: {version}.")
        return
    
    try:
        items_response = requests.get(final_url)
        return items_response.json()
    except requests.RequestException as e:
        print(f"An error occurred (item file): {e}")
        return

def get_strings_file(version, lang):
    urls = [f"data/menu/main_{lang}.stringtable.json", f"data/menu/fontconfig_{lang}.txt.json"]
    final_url = get_final_url(version, urls)

    if not final_url:
        print(f"Strings file not found: {version}:{lang}.")
        return
    
    try:
        items_response = requests.get(final_url)
        return items_response.json()["entries"]
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

    return False

def round_number(num, decimal, to_string=False):
    if isinstance(num, (int, float)):
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