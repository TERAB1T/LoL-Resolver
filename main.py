import argparse
import os
import shutil
import re
from lol.atlas import AtlasProcessor
from lol.generator import generate_lol_items
from tft.generator import generate_tft_units, generate_tft_traits, generate_tft_items, generate_tft_augments

def main():
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest="cmd")

    parser_items = subparsers.add_parser("lol-items", help="Generates League of Legends items.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")
    parser_items.add_argument("--icons", action=argparse.BooleanOptionalAction, default=False, help="Determines whether to generate item icons.")

    parser_items = subparsers.add_parser("tft", help="Generates Teamfight Tactics units, traits, items, and augments.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")

    parser_items = subparsers.add_parser("tft-units", help="Generates Teamfight Tactics units.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")

    parser_items = subparsers.add_parser("tft-traits", help="Generates Teamfight Tactics traits.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")

    parser_items = subparsers.add_parser("tft-items", help="Generates Teamfight Tactics items.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")

    parser_items = subparsers.add_parser("tft-augments", help="Generates Teamfight Tactics augments.")
    parser_items.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")

    parser_staticons = subparsers.add_parser("staticons", help="Generates stat icons used in tooltips for abilities, items, etc.")
    parser_staticons.add_argument("-v", "--version", nargs='+', metavar="VERSION", default="pbe", help="Version of the game (currently supported: >=11.1 and latest/pbe/all).")
    parser_staticons.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")

    args = arg_parser.parse_args()

    if args.cmd == "lol-items":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            generate_lol_items(version, output_dir, args.cache, args.icons)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd == "tft":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        
        for version in args.version:
            generate_tft_units(version, output_dir, args.cache)
            generate_tft_traits(version, output_dir, args.cache)
            generate_tft_items(version, output_dir, args.cache)
            generate_tft_augments(version, output_dir, args.cache)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd in ["tft-units", "tft-traits", "tft-items", "tft-augments"]:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)

        for version in args.version:
            match args.cmd:
                case "tft-units":
                    generate_tft_units(version, output_dir, args.cache)
                case "tft-traits":
                    generate_tft_traits(version, output_dir, args.cache)
                case "tft-items":
                    generate_tft_items(version, output_dir, args.cache)
                case "tft-augments":
                    generate_tft_augments(version, output_dir, args.cache)

            if re.match(r'^\d+\.\d+$', version) or version in ['latest', 'pbe']:
                rm_temp_cache(version)

    elif args.cmd == "staticons":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
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