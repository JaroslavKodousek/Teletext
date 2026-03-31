import json
import random
import urllib.request
from PIL import Image, ImageDraw, ImageFont
from staticmap import StaticMap

class MapPageGenerator:
    """Generates a random Czech map page for the PDF."""

    CZ_BOUNDS = {
        "lat": (48.55, 51.05),
        "lon": (12.09, 18.86)
    }

    def __init__(self, width=1072, height=1448):
        self.width = width
        self.height = height

    def _get_random_coordinates(self):
        """Returns random coordinates within the Czech Republic."""
        lat = random.uniform(*self.CZ_BOUNDS["lat"])
        lon = random.uniform(*self.CZ_BOUNDS["lon"])
        return lat, lon

    def _fetch_location_info(self, lat, lon):
        """Fetches reverse geocoded information for given coordinates using Nominatim API."""
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Teletext-Bot/1.0'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read())
                address = data.get('address', {})
                display_name = data.get('display_name', 'Neznámé místo')

                # Priority county
                kraj = address.get('county')
                if not kraj:
                    kraj = address.get('city') or address.get('town') or address.get('village', 'Neznámý kraj')

                short_address = kraj
                
                return short_address, display_name
        except Exception as e:
            print(f"Error fetching address: {e}")
            return "Neznámé místo", "Neznámé místo"

    def generate_map_page(self):
        """
        Generates the map page image with a random map of Czechia and address info.

        Returns:
            PIL.Image: The generated last page image.
        """
        lat, lon = self._get_random_coordinates()
        short_address, full_address = self._fetch_location_info(lat, lon)

        # 1. Create a base white image
        img = Image.new("L", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)

        # 2. Select fonts
        font_names = ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "FreeSansBold.ttf", "LiberationSans-Bold.ttf"]
        
        font_large = font_medium = font_small = None
        for font_name in font_names:
            try:
                font_large = ImageFont.truetype(font_name, 60)
                font_medium = ImageFont.truetype(font_name, 40)
                font_small = ImageFont.truetype(font_name, 24)
                break
            except OSError:
                continue

        if font_large is None:
            try:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except TypeError:
                pass


        # 3. Draw headers
        header_text = "Křížem krážem Českem"
        try:
            bbox = font_large.getbbox(header_text)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width = draw.textlength(header_text, font=font_large)

        x = (self.width - text_width) // 2
        y_offset = 120
        draw.text((x, y_offset), header_text, font=font_large, fill=0)
        y_offset += 120

        # Draw the short address below header
        try:
            bbox_addr = font_medium.getbbox(short_address)
            addr_width = bbox_addr[2] - bbox_addr[0]
        except AttributeError:
            addr_width = draw.textlength(short_address, font=font_medium)
            
        x_addr = (self.width - addr_width) // 2
        draw.text((x_addr, y_offset), short_address, font=font_medium, fill=0)
        y_offset += 60

        # Draw the coordinates below the address
        coords_text = f"GPS: {lat:.5f}N, {lon:.5f}E"
        try:
            bbox_coords = font_small.getbbox(coords_text)
            coords_width = bbox_coords[2] - bbox_coords[0]
        except AttributeError:
            coords_width = draw.textlength(coords_text, font=font_small)
            
        x_coords = (self.width - coords_width) // 2
        draw.text((x_coords, y_offset), coords_text, font=font_small, fill=0)
        y_offset += 60

        # 4. Generate the Map (Zoom 11 is usually good for showing a town and its surroundings)
        map_width = self.width - 100
        map_height = self.height - y_offset - 100
        
        print(f"Generating random map for {lat:.4f}, {lon:.4f} in {short_address}...")
        m = StaticMap(map_width, map_height, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
        map_image = m.render(zoom=11, center=[lon, lat])
        
        # Convert to black and white or grayscale to match teletext style if needed,
        # but the prompt implies we can keep it standard. Let's make it grayscale 
        # to ensure it looks good with the PDF grayscale style.
        map_image = map_image.convert("L")

        # Paste the map into the base image
        img.paste(map_image, (50, y_offset))

        return img

if __name__ == "__main__":
    generator = MapPageGenerator()
    img = generator.generate_map_page()
    img.save("test_map_page.png")
    print("Test page generated as test_map_page.png")
