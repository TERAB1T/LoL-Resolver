import argparse
import os
import shutil
import re
from utils import cd_get_versions_clean
from lol.atlas import AtlasProcessor
from lol.generator import generate_lol_items
from rgm.generator import generate_swarm_augments
from tft.generator import generate_tft_units, generate_tft_traits, generate_tft_items, generate_tft_augments

def main():
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest="cmd")

    parser_items = subparsers.add_parser("lol-items", help="Generates League of Legends items.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")
    parser_items.add_argument("--icons", action=argparse.BooleanOptionalAction, default=False, help="Generate item icons.")

    parser_items = subparsers.add_parser("swarm-augments", help="Generates LoL Swarm augments.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_items = subparsers.add_parser("tft", help="Generates Teamfight Tactics units, traits, items, and augments.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_items = subparsers.add_parser("tft-units", help="Generates Teamfight Tactics units.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_items = subparsers.add_parser("tft-traits", help="Generates Teamfight Tactics traits.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_items = subparsers.add_parser("tft-items", help="Generates Teamfight Tactics items.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_items = subparsers.add_parser("tft-augments", help="Generates Teamfight Tactics augments.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_items.add_argument("-l", "--lang", nargs='+', metavar="LANGUAGE", default=["all"], help="Language of the game (e.g., en_us, ru_ru, zh_cn, all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Use Redis cache.")

    parser_staticons = subparsers.add_parser("staticons", help="Generates stat icons used in tooltips for abilities, items, etc.")
    parser_staticons.add_argument("-v", "--version", nargs='+', metavar="VERSION", default=["pbe"], help="Version of the game (e.g., 11.1, 13.23, latest, pbe, all).")
    parser_staticons.add_argument("-o", "--output", metavar="PATH", default="export", help="Output path.")

    args = arg_parser.parse_args()

    if args.cmd == "lol-items":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        
        if args.version[0] == 'all':
            args.version = cd_get_versions_clean()

        for version in args.version:
            generate_lol_items(version, output_dir, args.lang, args.cache, args.icons)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd == "swarm-augments":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        
        if args.version[0] == 'all':
            args.version = cd_get_versions_clean()

        for version in args.version:
            generate_swarm_augments(version, output_dir, args.lang, args.cache)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd == "tft":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)

        if args.version[0] == 'all':
            args.version = cd_get_versions_clean()
        
        for version in args.version:
            generate_tft_units(version, output_dir, args.lang, args.cache)
            generate_tft_traits(version, output_dir, args.lang, args.cache)
            generate_tft_items(version, output_dir, args.lang, args.cache)
            generate_tft_augments(version, output_dir, args.lang, args.cache)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd in ["tft-units", "tft-traits", "tft-items", "tft-augments"]:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)

        if args.version[0] == 'all':
            args.version = cd_get_versions_clean()

        for version in args.version:
            match args.cmd:
                case "tft-units":
                    generate_tft_units(version, output_dir, args.lang, args.cache)
                case "tft-traits":
                    generate_tft_traits(version, output_dir, args.lang, args.cache)
                case "tft-items":
                    generate_tft_items(version, output_dir, args.lang, args.cache)
                case "tft-augments":
                    generate_tft_augments(version, output_dir, args.lang, args.cache)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd == "staticons":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)

        if args.version[0] == 'all':
            args.version = cd_get_versions_clean()

        for version in args.version:
            AtlasProcessor().process_staticons(version, output_dir)

    else:
        arg_parser.print_help()

    rm_temp_cache()

def rm_temp_cache(version=''):
    temp_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_temp', version)

    if os.path.exists(temp_cache_dir):
        shutil.rmtree(temp_cache_dir)

if __name__ == "__main__":
    main()