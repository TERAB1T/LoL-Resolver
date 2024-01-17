import argparse
import os
from items.atlas_processor import AtlasProcessor
from items.items_processor import ItemsProcessor
from items.items_generator import generate_items

def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-i", "--items", default="pbe", metavar="VERSION", help="Generates items using the specified version of the game (currently supported: latest/pbe/all).")
    argParser.add_argument("-o", "--output", metavar="PATH", default="export", help="Defines the output path.")
    argParser.add_argument("--cache", action=argparse.BooleanOptionalAction, default=False, help="Determines whether the Redis cache should be used.")
    argParser.add_argument("--itemicons", action=argparse.BooleanOptionalAction, default=False, help="Determines whether to generate item icons.")
    args = argParser.parse_args()

    if args.items:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
        generate_items(args.items, output_dir, args.cache, args.itemicons)


if __name__ == "__main__":
    main()