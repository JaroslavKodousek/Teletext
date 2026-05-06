import os
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw, ImageFont

from src.first_page import FirstPageGenerator
from src.map_page import MapPageGenerator
from src.wiki_page import WikiPageGenerator


class DownloadTeletext:
    """Handles downloading and processing teletext images."""

    API_URL_TEMPLATE = "https://api-teletext.ceskatelevize.cz/pages/{page}/image.webp"

    def __init__(self, page_ranges=None):
        if page_ranges is None:
            page_ranges = [(100, 170), (600, 620)]  # Default ranges
        self.page_ranges = page_ranges
        self.saved_images = []
        self.pdf_path = None

    def download_and_create_pdf(self):
        """
        Downloads teletext page images and creates a PDF containing all valid images.

        Returns:
            str or None: The file path to the created PDF if images were saved, otherwise None.
        """
        self._create_data_folder()
        folder_name, folder_name_images = self._setup_folders()
        self._download_images(folder_name_images)
        return self._create_pdf(folder_name)

    def _create_data_folder(self):
        """Ensures the data folder exists."""
        if not os.path.isdir("data"):
            os.makedirs("data")

    def _setup_folders(self):
        """Creates timestamped folders for storing images and PDFs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = os.path.join("data", f"{timestamp}_teletext")
        os.makedirs(folder_name, exist_ok=True)
        folder_name_images = os.path.join(folder_name, "images")
        os.makedirs(folder_name_images, exist_ok=True)
        return folder_name, folder_name_images

    def _download_images(self, folder_name_images):
        """Downloads and processes teletext images for all ranges."""
        for start, end in self.page_ranges:
            for page in range(start, end):
                self._download_single_page(page, folder_name_images)

    def _download_single_page(self, page, folder_name_images):
        """Downloads and processes a single teletext page."""
        page_str = str(page)
        url = self.API_URL_TEMPLATE.format(page=page_str)

        response = self._fetch_url(url)
        if response is None or response.status_code != 200:
            fallback_page = f"{page_str}A"
            fallback_url = self.API_URL_TEMPLATE.format(page=fallback_page)
            print(f"Primary URL failed for page {page_str}; trying fallback {fallback_page}")
            response = self._fetch_url(fallback_url)
            page_str = fallback_page

        if response is not None and response.status_code == 200:
            self._process_image(response.content, page_str, folder_name_images)
        else:
            status = response.status_code if response is not None else 'no-response'
            print(f"Failed to retrieve page {page_str}: {status}")

    def _fetch_url(self, url):
        """Fetches a URL and returns the response if successful."""
        try:
            return requests.get(url, timeout=10)
        except requests.RequestException as exc:
            print(f"Request failed for {url}: {exc}")
            return None

    def _process_image(self, image_data, page, folder_name_images):
        """Processes a downloaded image and saves it if it's not uniform."""
        try:
            img = Image.open(BytesIO(image_data))
        except Exception as exc:
            print(f"Failed to open image for page {page}: {exc}")
            return

        img = img.convert("L")

        # Apply binarization
        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0)
        img = ImageOps.invert(img)

        # Check if image is uniform
        pixels = list(img.getdata())
        if pixels and all(pixel == pixels[0] for pixel in pixels):
            print(f"Skipped uniform color image for page {page}")
            return

        # Add page number and padding
        img = self._add_page_number(img, page)
        img = self._add_padding(img)

        # Save image
        img_path = os.path.join(folder_name_images, f"teletext_{page}.png")
        img.save(img_path, format="PNG")
        self.saved_images.append(img_path)

    def _add_page_number(self, img, page):
        """Adds a page number to the bottom of the image."""
        extra_height = 20
        new_img = Image.new("L", (img.width, img.height + extra_height), 255)
        new_img.paste(img, (0, 0))

        draw = ImageDraw.Draw(new_img)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()

        text = f"Page {page}"
        bbox = font.getbbox(text)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (new_img.width - text_width) // 2
        y = img.height + (extra_height - text_height) // 2
        draw.text((x, y), text, font=font, fill=0)

        return new_img

    def _add_padding(self, img):
        """Adds padding around the image."""
        padding = 10
        padded_img = Image.new(
            "L", (img.width + 2 * padding, img.height + 2 * padding), 255
        )
        padded_img.paste(img, (padding, padding))
        return padded_img

    def _create_pdf(self, folder_name):
        """Creates a PDF from all saved images."""
        date_str = datetime.now().strftime("%d.%m.%Y")
        pdf_filename = f"Teletext {date_str}.pdf"
        pdf_path = os.path.join(folder_name, pdf_filename)

        # Generate first page with greeting
        first_page_gen = FirstPageGenerator()
        first_page = first_page_gen.generate_first_page().convert("RGB")

        # Generate map page
        map_page_gen = MapPageGenerator()
        map_page = map_page_gen.generate_map_page().convert("RGB")

        # Generate wikipedia pages
        wiki_en_gen = WikiPageGenerator(lang="en")
        wiki_en_page = wiki_en_gen.generate_wiki_page().convert("RGB")
        
        wiki_cs_gen = WikiPageGenerator(lang="cs")
        wiki_cs_page = wiki_cs_gen.generate_wiki_page().convert("RGB")

        # Combine first page, images, and appendix pages
        image_objs = [first_page]
        if self.saved_images:
            image_objs += [
                Image.open(img_path).convert("RGB") for img_path in self.saved_images
            ]
        image_objs += [map_page, wiki_en_page, wiki_cs_page]
        
        image_objs[0].save(pdf_path, save_all=True, append_images=image_objs[1:])
        
        if not self.saved_images:
            print(f"No teletext images saved, but PDF created at {pdf_path} (first page, map, wiki).")
        else:
            print(f"PDF created at {pdf_path}")
            
        self.pdf_path = pdf_path
        return pdf_path
