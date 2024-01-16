import os
import requests
from io import BytesIO
from PIL import Image
import struct

class AtlasProcessor:
    def __init__(self):
        pass

    def parse_struct(self, data):
        parsed_data = {}

        parsed_data['file_count'] = int.from_bytes(data[:4], byteorder='little')
        parsed_data['filename_length'] = int.from_bytes(data[4:8], byteorder='little')
        parsed_data['filename'] = data[8:8 + parsed_data['filename_length']].decode('utf-8')
        offset = 8 + parsed_data['filename_length']

        parsed_data['entry_count'] = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        parsed_data['entries'] = []
        for i in range(parsed_data['entry_count']):
            entry_name_length, = struct.unpack('I', data[offset:offset + 4])
            offset += 4

            entry_name = data[offset:offset + entry_name_length].decode('utf-8')
            offset += entry_name_length

            entry = {
                'entry_name': entry_name,
                'x_start_percentage': struct.unpack('f', data[offset:offset + 4])[0],
                'y_start_percentage': struct.unpack('f', data[offset + 4:offset + 8])[0],
                'x_end_percentage': struct.unpack('f', data[offset + 8:offset + 12])[0],
                'y_end_percentage': struct.unpack('f', data[offset + 12:offset + 16])[0],
                'containing_file_index': int.from_bytes(data[offset + 16:offset + 20], byteorder='little')
            }
            offset += 20
            parsed_data['entries'].append(entry)

        return parsed_data

    def split_icons_from_atlas(self, atlas_file, parsed_data):
        try:
            response = requests.get(atlas_file)
            if response.status_code != 200:
                print("Failed to fetch the PNG atlas file.")
                return
            
            atlas_image = Image.open(BytesIO(response.content))

            for entry in parsed_data['entries']:
                x_start_percentage = entry['x_start_percentage']
                y_start_percentage = entry['y_start_percentage']
                x_end_percentage = entry['x_end_percentage']
                y_end_percentage = entry['y_end_percentage']

                width, height = atlas_image.size
                x_start = int(x_start_percentage * width)
                y_start = int(y_start_percentage * height)
                x_end = int(x_end_percentage * width)
                y_end = int(y_end_percentage * height)

                icon_width = x_end - x_start
                icon_height = y_end - y_start

                icon_image = atlas_image.crop((x_start, y_start, x_end, y_end))
                entry_name = os.path.splitext(os.path.basename(entry['entry_name']))[0].lower()
                output_file = os.path.join(self.output_dir, f"{entry_name}.webp")
                
                icon_image.save(output_file, 'WEBP', quality=95)
        except Exception as e:
            print(f"An error occurred: {e}")

    def process_icons(self, version, output_dir):
        self.output_dir = os.path.join(output_dir, f"items/{version}/icons")
        os.makedirs(self.output_dir, exist_ok=True)

        url_bin = f"https://raw.communitydragon.org/{version}/game/assets/items/icons2d/autoatlas/largeicons/atlas_info.bin"
        response = requests.get(url_bin)
        
        if response.status_code != 200:
            print(f"Atlas file not found: {version}")
            return
        
        binary_data = response.content
        parsed_data = self.parse_struct(binary_data)
        atlas_file = f"https://raw.communitydragon.org/{version}/game/assets/items/icons2d/autoatlas/largeicons/atlas_0.png"
        self.split_icons_from_atlas(atlas_file, parsed_data)