import os
import re
import ujson
import redis
import aiohttp
import asyncio
import urllib3
from io import BytesIO
from PIL import Image, ImageOps
from typing import Dict, List, Set, Tuple
from tqdm.asyncio import tqdm
from utils import cd_get_versions, get_last_modified
from constants import REDIS_PREFIX, REDIS_HOST, REDIS_PORT

class ThumbGenerator:
    def __init__(self,
                 version: str,
                 output_dir: str,
                 cache: bool):
        self.version = version
        self.output_dir = os.path.join(output_dir, 'thumbs') # TEMP!!!
        self.is_cache_needed = cache

        self.last_modified: str | None = None
        self.redis = None if not cache else self.__init_redis()
        self.redis_versions: Dict[str, str] = {}
        self.redis_images: Dict[str, str] = {}
        self.is_cache_exists = False

        self.redis_key_images = f"{REDIS_PREFIX}:thumbs:images"
        self.redis_key_versions = f"{REDIS_PREFIX}:thumbs:versions"

        if not self.__validate_version():
            return

        if self.is_cache_needed:
            self.__get_global_cache()

        if not self.is_cache_exists:
            self.__process_thumbnails((
                ("lol-skins", "v1/skins.json", [(50, 50), (100, 100)]),
                ("tft-arenas", "v1/tftmapskins.json", [(100, 100)]),
                ("tft-booms", "v1/tftdamageskins.json", [(100, 100)]),
                ("tft-tactics", "v1/companions.json", [(100, 100)])
            ))

            if self.is_cache_needed and self.redis:
                    self.redis.hset(self.redis_key_images, mapping=self.redis_images)
                    self.redis.hset(self.redis_key_versions, mapping=self.redis_versions)
    

    def __init_redis(self) -> redis.Redis | None:
        try:
            redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            redis_client.ping()
            return redis_client
        except Exception:
            return None
    

    def __validate_version(self) -> bool:
        if re.match(r'^\d+\.\d+$', self.version):
            versions = cd_get_versions()
            version_info = next((element for element in versions if element['name'] == self.version), None)

            if version_info:
                self.last_modified = version_info.get('mtime')
                return True
        elif self.version in ['latest', 'pbe']:
            if self.is_cache_needed:
                self.last_modified = get_last_modified(self.version, '')

                if not self.last_modified:
                    print(f"Version {self.version} not found.")
                    return False
                
            return True
        
        print(f"Invalid or not found version: {self.version}")
        return False


    def __get_global_cache(self) -> None:
        if not self.redis:
            return

        self.redis_versions = self.redis.hgetall(self.redis_key_versions)
        self.redis_images = self.redis.hgetall(self.redis_key_images)
        
        if self.version not in self.redis_versions:
            self.redis_versions[self.version] = ''

        if re.match(r'^\d+\.\d+$', self.version):
            if self.redis_versions[self.version] == self.last_modified:
                self.is_cache_exists = True
                print(f"Thumbnails: version {self.version} is up to date. Skipping...")
            else:
                self.redis_versions[self.version] = self.last_modified
        elif self.version in ['latest', 'pbe']:
            version_modified = "live" if self.version == "latest" else self.version
            response = urllib3.request("GET", f"https://raw.communitydragon.org/status.{version_modified}.txt")

            if response.status == 200:
                patch_status = response.data.decode('utf-8')
            else:
                return
            
            if "done" in patch_status:
                if self.redis_versions[self.version] != self.last_modified:
                    self.redis_versions[self.version] = self.last_modified
                else:
                    self.is_cache_exists = True
                    print(f"Thumbnails: version {self.version} is up to date. Skipping...")
            elif "running" in patch_status:
                self.is_cache_exists = True
                print(f"Thumbnails - version {self.version}: CDragon is currently being updated. Please try again later.")
            elif "error" in patch_status:
                self.is_cache_exists = True
                print(f"Thumbnails - version {self.version}: The latest CDragon update failed. Please try again later.")
    

    def __process_thumbnails(self, categories: Tuple[str, str, List[Tuple[int, int]]]) -> None:
        for alias, endpoint, sizes in categories:
            url = f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/{endpoint}"
            response = urllib3.request("GET", url)
            if response.status != 200:
                continue
            
            output_dir = os.path.join(self.output_dir, alias)
            os.makedirs(output_dir, exist_ok=True)
            
            raw_data = ujson.loads(response.data)
            urls = self.__extract_image_urls(alias, raw_data)
            asyncio.run(self.__process_urls(urls, sizes, output_dir, alias))


    def __extract_image_urls(self, alias: str, raw_data) -> Set[str]:
        urls = set()
        for entry in raw_data if isinstance(raw_data, list) else raw_data.values():
            if alias == "lol-skins":
                urls.add(self.__convert_url(entry.get("tilePath")))
                for tier in (entry.get("questSkinInfo", {}).get("tiers", [])):
                    urls.add(self.__convert_url(tier.get("tilePath")))
            else:
                urls.add(self.__convert_url(entry.get("loadoutsIcon")))
        return {url for url in urls if url}
    

    def __convert_url(self, path: str) -> str:
        return path.lower().replace("/lol-game-data/assets/", f"https://raw.communitydragon.org/{self.version}/plugins/rcp-be-lol-game-data/global/default/") if path else ""
    

    async def __process_urls(self,
                            urls: Set[str],
                            sizes: List[Tuple[int, int]],
                            output_dir: str,
                            alias: str) -> None:
        semaphore = asyncio.Semaphore(20)
        with tqdm(total=len(urls), desc=f"Generating thumbnails ({alias})", unit="image", bar_format="{desc}: {n_fmt}/{total_fmt} |{bar:20}|") as pbar:
            tasks = [self.__process_image(url, sizes, output_dir, alias, semaphore, pbar) for url in urls]
            await asyncio.gather(*tasks)


    async def __process_image(self,
                             url: str,
                             sizes: List[Tuple[int, int]],
                             output_dir: str,
                             alias: str,
                             semaphore: asyncio.Semaphore,
                             pbar: tqdm) -> None:
        img_without_extension = os.path.splitext(os.path.basename(url))[0]
        async with semaphore:
            async def inner_process_image(session: aiohttp.ClientSession) -> None:
                async with session.get(url) as response:
                    if response.status == 200:
                        for size in sizes:
                            img = await response.read()
                            img = Image.open(BytesIO(img))
                            img = ImageOps.fit(img, size, Image.LANCZOS)
                            img.save(f"{output_dir}/{img_without_extension}_{size[0]}x{size[1]}.webp", "WEBP")
                            img.close()

            async with aiohttp.ClientSession() as session:
                if self.is_cache_needed:
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