import os
import ujson
from utils import *
import aiohttp
import asyncio
from io import BytesIO
from PIL import Image, ImageOps
from tqdm.asyncio import tqdm

class ThumbGenerator:
    def __init__(self, version, output_dir, cache):
        self.version = version
        self.output_dir = os.path.join(output_dir, f"thumbs") # TEMP!!!
        self.cache = cache

        self.last_modified = None
        self.redis_con = None
        self.redis_global = {}
        self.redis_images = {}
        self.is_cached = False

        if re.match(r'^\d+\.\d+$', self.version):
            versions = cd_get_versions()
            version = next((element for element in versions if element['name'] == self.version), None)

            if version:
                self.last_modified = version.get('mtime')
            else:
                print(f"Version {self.version} not found.")
                return
        elif self.version in ['latest', 'pbe']:
            if cache:
                self.last_modified = get_last_modified(self.version, '')

                if not self.last_modified:
                    print(f"Version {self.version} not found.")
                    return
        else:
            print("Invalid version.")
            return

        if cache:
            self._get_global_cache()

        if not self.is_cached:
            self._process_lol_skins()
            self._process_tft_arenas()
            self._process_tft_booms()
            self._process_tft_tactics()

        if cache:
            if self.redis_con:
                self.redis_con.set("thumb-images", ujson.dumps(self.redis_images))
    
    def _get_global_cache(self):
        try:
            if self.cache:
                self.redis_con = redis.Redis(host='localhost', port=6379, decode_responses=True)
                self.redis_con.ping()
        except:
            self.redis_con = None

        if self.redis_con and self.redis_con.exists("thumb-versions"):
            self.redis_global = ujson.loads(self.redis_con.get("thumb-versions"))

        if self.redis_con and self.redis_con.exists("thumb-images"):
            self.redis_images = ujson.loads(self.redis_con.get("thumb-images"))

        if re.match(r'^\d+\.\d+$', self.version):
            if self.version not in self.redis_global or 'last_modified' not in self.redis_global[self.version]:
                self.redis_global[self.version] = {
                    "last_modified": ''
                }
            
            if self.redis_global[self.version]["last_modified"] == self.last_modified:
                self.is_cached = True
                print(f"Version {self.version} is up to date. Skipping...")
            else:
                if self.redis_con:
                    self.redis_global[self.version]["last_modified"] = self.last_modified
                    self.redis_con.set("thumb-versions", ujson.dumps(self.redis_global))
        elif self.version in ['latest', 'pbe']:
            if self.version not in self.redis_global or 'status' not in self.redis_global[self.version] or 'last_modified' not in self.redis_global[self.version]:
                self.redis_global[self.version] = {
                    "status": '',
                    "last_modified": ''
                }

            version_modified = "live" if self.version == "latest" else self.version
            response = urllib3.request("GET", f"https://raw.communitydragon.org/status.{version_modified}.txt")

            if response.status == 200:
                patch_status = response.data.decode('utf-8')
            else:
                return
            
            if self.redis_global[self.version]["status"] != patch_status and "done" in patch_status:
                if self.redis_global[self.version]["last_modified"] != self.last_modified:

                    if self.redis_con:
                        self.redis_global[self.version]["status"] = patch_status
                        self.redis_global[self.version]["last_modified"] = self.last_modified
                        self.redis_con.set("thumb-versions", ujson.dumps(self.redis_global))
                else:
                    self.is_cached = True
                    print(f"Version {self.version} is up to date. Skipping...")
            elif self.redis_global[self.version]["status"] == patch_status:
                self.is_cached = True
                print(f"Version {self.version} is up to date. Skipping...")
            elif "running" in patch_status:
                self.is_cached = True
                print(f"Version {self.version}: CDragon is currently being updated. Please try again later.")
            elif "error" in patch_status:
                self.is_cached = True
                print(f"Version {self.version}: The latest CDragon update failed. Please try again later.")
    
    async def _process_urls(self, urls, sizes, output_dir, alias):
        semaphore = asyncio.Semaphore(20)
        with tqdm(total=len(urls), desc=f"Generating thumbnails ({alias})", unit="image", bar_format="{desc}: {n_fmt}/{total_fmt} |{bar:20}|") as pbar:
            tasks = [self._process_image(url, sizes, output_dir, alias, semaphore, pbar) for url in urls]
            await asyncio.gather(*tasks)

    async def _process_image(self, url, sizes, output_dir, alias, semaphore, pbar):
        img_without_extension = os.path.splitext(os.path.basename(url))[0]
        async with semaphore:
            async def inner_process_image(session):
                async with session.get(url) as response:
                    if response.status == 200:
                        for size in sizes:
                            img = await response.read()
                            img = Image.open(BytesIO(img))
                            img = ImageOps.fit(img, size, Image.LANCZOS)
                            img.save(f"{output_dir}/{img_without_extension}_{size[0]}x{size[1]}.webp", "WEBP")
                            img.close()

            async with aiohttp.ClientSession() as session:
                if self.cache:
                    async with session.head(url, headers={'Cache-Control': 'no-cache'}) as head_response:
                        if head_response.status == 200:
                            image_last_modified = head_response.headers.get('Last-Modified')
                            image_name = f"{alias}:{img_without_extension}"

                            cache_last_modified = self.redis_images.get(image_name, '')

                            if cache_last_modified != image_last_modified:
                                self.redis_images[image_name] = image_last_modified

                                await inner_process_image(session)
                                
                else:        
                    await inner_process_image(session)
        pbar.update(1)

    ### TYPES ###

    def _process_lol_skins(self):
        alias = "lol-skins"
        url = f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/v1/skins.json"
        response = urllib3.request("GET", url)

        if response.status == 200:
            output_dir = os.path.join(self.output_dir, alias)
            os.makedirs(output_dir, exist_ok=True)

            raw_data = ujson.loads(response.data)
            output_list = set()

            for entry in raw_data.values():
                img_path = entry.get("tilePath", "").lower().replace("/lol-game-data/assets/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/assets/")
                output_list.add(img_path)

                alt_versions = entry.get("questSkinInfo")

                if alt_versions:
                    alt_versions_tiers = alt_versions.get("tiers", [])

                    for alt_version in alt_versions_tiers:
                        img_path = alt_version.get("tilePath", "").lower().replace("/lol-game-data/assets/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/assets/")
                        output_list.add(img_path)

            asyncio.run(self._process_urls(output_list, [[50, 50], [100, 100]], output_dir, alias))

    def _process_tft_arenas(self):
        alias = "tft-arenas"
        url = f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/v1/tftmapskins.json"
        response = urllib3.request("GET", url)

        if response.status == 200:
            output_dir = os.path.join(self.output_dir, alias)
            os.makedirs(output_dir, exist_ok=True)

            raw_data = ujson.loads(response.data)
            output_list = set()

            for entry in raw_data:
                img_path = entry.get("loadoutsIcon", "").lower().replace("/lol-game-data/assets/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/assets/")
                output_list.add(img_path)

            asyncio.run(self._process_urls(output_list, [[100, 100]], output_dir, alias))

    def _process_tft_booms(self):
        alias = "tft-booms"
        url = f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/v1/tftdamageskins.json"
        response = urllib3.request("GET", url)

        if response.status == 200:
            output_dir = os.path.join(self.output_dir, alias)
            os.makedirs(output_dir, exist_ok=True)

            raw_data = ujson.loads(response.data)
            output_list = set()

            for entry in raw_data:
                img_path = entry.get("loadoutsIcon", "").lower().replace("/lol-game-data/assets/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/assets/")
                output_list.add(img_path)

            asyncio.run(self._process_urls(output_list, [[100, 100]], output_dir, alias))

    def _process_tft_tactics(self):
        alias = "tft-tactics"
        url = f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/v1/companions.json"
        response = urllib3.request("GET", url)

        if response.status == 200:
            output_dir = os.path.join(self.output_dir, alias)
            os.makedirs(output_dir, exist_ok=True)

            raw_data = ujson.loads(response.data)
            output_list = set()

            for entry in raw_data:
                img_path = entry.get("loadoutsIcon", "").lower().replace("/lol-game-data/assets/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/assets/")
                output_list.add(img_path)

            asyncio.run(self._process_urls(output_list, [[100, 100]], output_dir, alias))