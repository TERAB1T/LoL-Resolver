import argparse
import os
from items.atlas_processor import AtlasProcessor
from items.items_processor import ItemsProcessor
from items.items_generator import generate_items

def main():
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest="cmd")

    parser_items = subparsers.add_parser("items", help="Generates League of Legends items.")
    parser_items.add_argument("-v", "--version", metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_items.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    parser_items.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")
    parser_items.add_argument("--itemicons", action=argparse.BooleanOptionalAction, default=False, help="Determines whether to generate item icons.")

    parser_staticons = subparsers.add_parser("staticons", help="Generates stat icons used in tooltips for abilities, items, etc.")
    parser_staticons.add_argument("-v", "--version", metavar="VERSION", default="pbe", help="Version of the game (currently supported: latest/pbe/all).")
    parser_staticons.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")

    args = arg_parser.parse_args()

    if args.cmd == "items":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        generate_items(args.version, output_dir, args.cache, args.itemicons)
    elif args.cmd == "staticons":
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        AtlasProcessor().process_staticons(args.version, output_dir)
    else:
        arg_parser.print_help()


if __name__ == "__main__":
    main()