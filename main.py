import argparse
import os
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

    elif args.cmd == "tft-units":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            generate_tft_units(version, output_dir, args.cache)

    elif args.cmd == "tft-traits":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            generate_tft_traits(version, output_dir, args.cache)

    elif args.cmd == "tft-items":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            generate_tft_items(version, output_dir, args.cache)

    elif args.cmd == "tft-augments":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            generate_tft_augments(version, output_dir, args.cache)

    elif args.cmd == "staticons":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        for version in args.version:
            AtlasProcessor().process_staticons(version, output_dir)

    else:
        arg_parser.print_help()


if __name__ == "__main__":
    main()