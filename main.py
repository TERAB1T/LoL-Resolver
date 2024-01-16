import argparse
import os
from items.atlas_processor import AtlasProcessor
from items.items_processor import ItemsProcessor
from items.items_generator import generate_items

def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"export")
    generate_items("pbe", output_dir, True, True)

    # argParser = argparse.ArgumentParser()
    # argParser.add_argument("-i", "--items", default="pbe", metavar="VERSION", help="Generates items using the # specified version of the game.")
	# argParser.add_argument("-o", "--output", metavar="PATH", help="Generates items using the # specified version of the game.")
    # args = argParser.parse_args()
    # 
    # if args.items:
    #     version = args.items
    #     ItemsProcessor(version, "ru_ru")
    
    # processor = AtlasProcessor()
    # processor.process_icons(version)


if __name__ == "__main__":
    main()