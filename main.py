import argparse
import os
import shutil
import re
from utils import cd_get_versions_clean, timer_func
from lol.atlas import AtlasProcessor
from lol.generator import generate_lol_champions, generate_lol_items, generate_arena_augments, generate_swarm_augments
from tft.generator import generate_tft_units, generate_tft_traits, generate_tft_items, generate_tft_augments, generate_tocker_rounds, generate_tft_anomaly

def rm_temp_cache(version: str = '') -> None:
    #return
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_temp', version)

    if os.path.exists(temp_cache_dir):
        shutil.rmtree(temp_cache_dir)

@timer_func
def main():
    # TFT Tocker's Trials rounds
    # generate_tocker_rounds('pbe', 'export', ['all'], False)

    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest="cmd")

    cmd_configs = {
        "lol": {"help": "Generates League of Legends items, Arena augments, and Swarm augments.", "func": generate_lol_all, "extra_args": {"--icons": {"action": argparse.BooleanOptionalAction, "default": False, "help": "Generate item icons."}}},
        "lol-champions": {"help": "Generates League of Legends champions.", "func": generate_lol_champions},
        "lol-items": {"help": "Generates League of Legends items.", "func": generate_lol_items, "extra_args": {"--icons": {"action": argparse.BooleanOptionalAction, "default": False, "help": "Generate item icons."}}},
        "tft": {"help": "Generates Teamfight Tactics units, traits, items, and augments.", "func": generate_tft_all},
        "tft-units": {"help": "Generates Teamfight Tactics units.", "func": generate_tft_units},
        "tft-traits": {"help": "Generates Teamfight Tactics traits.", "func": generate_tft_traits},
        "tft-items": {"help": "Generates Teamfight Tactics items.", "func": generate_tft_items},
        "tft-augments": {"help": "Generates Teamfight Tactics augments.", "func": generate_tft_augments},
        "tft-anomaly": {"help": "Generates Teamfight Tactics anomaly effects (set 13).", "func": generate_tft_anomaly},
        "arena-augments": {"help": "Generates Arena augments.", "func": generate_arena_augments},
        "swarm-augments": {"help": "Generates Swarm augments.", "func": generate_swarm_augments},
        "staticons": {"help": "Generates stat icons used in tooltips for abilities, items, etc.", "func": process_staticons}
    }

    for cmd, config in cmd_configs.items():
        parser = subparsers.add_parser(cmd, help=config["help"])
        add_common_args(parser)
        if "extra_args" in config:
            for arg, kwargs in config["extra_args"].items():
                parser.add_argument(arg, **kwargs)

    args = arg_parser.parse_args()

    if args.cmd in cmd_configs:
        extra_args = []
        if args.cmd == "lol-items" or args.cmd == "lol":
            extra_args.append(args.icons)

        process_versions(args, cmd_configs[args.cmd]["func"], *extra_args)
    else:
        arg_parser.print_help()

    rm_temp_cache()

def add_common_args(parser_items: argparse.ArgumentParser) -> None:
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

def handle_versions(args: argparse.Namespace) -> list[str]:
    if args.version[0] == 'all':
        args.version = cd_get_versions_clean()
    return args.version

def process_versions(args, generate_func, *extra_args):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
    versions = handle_versions(args)
    for version in versions:
        generate_func(version, output_dir, args.lang, args.cache, *extra_args)
        if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
            rm_temp_cache(version)

def generate_lol_all(version, output_dir, lang, cache, icons):
    generate_lol_champions(version, output_dir, lang, cache)
    generate_lol_items(version, output_dir, lang, cache, icons)
    generate_arena_augments(version, output_dir, lang, cache)
    generate_swarm_augments(version, output_dir, lang, cache)

def generate_tft_all(version, output_dir, lang, cache):
    generate_tft_units(version, output_dir, lang, cache)
    generate_tft_traits(version, output_dir, lang, cache)
    generate_tft_items(version, output_dir, lang, cache)
    generate_tft_augments(version, output_dir, lang, cache)
    generate_tft_anomaly(version, output_dir, lang, cache)

def process_staticons(version, output_dir, lang, cache):
    AtlasProcessor().process_staticons(version, output_dir)

if __name__ == "__main__":
    main()