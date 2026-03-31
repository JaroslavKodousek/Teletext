import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont

class WikiPageGenerator:
    """Generates a page with a random Wikipedia article."""

    def __init__(self, lang="en", width=1072, height=1448):
        self.lang = lang
        self.width = width
        self.height = height

    def _fetch_random_article(self):
        """Fetches a random article's title, text, and constructs its URL."""
        url = f"https://{self.lang}.wikipedia.org/w/api.php?action=query&format=json&generator=random&grnnamespace=0&prop=extracts&exlimit=1&explaintext=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Teletext-Bot/1.0'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read())
                pages = data.get('query', {}).get('pages', {})
                if not pages:
                    return "Nelze načíst / Failed to load", "Neznámý obsah", ""
                
                # Get the first (and only) page object
                page = list(pages.values())[0]
                title = page.get('title', 'Neznámý')
                extract = page.get('extract', '...')
                pageid = page.get('pageid', '')
                
                article_url = f"https://{self.lang}.wikipedia.org/?curid={pageid}" if pageid else ""
                
                return title, extract, article_url
        except Exception as e:
            print(f"Error fetching Wikipedia ({self.lang}): {e}")
            return "Chyba / Error", "Něco se pokazilo. / Something went wrong.", ""

    def _wrap_text(self, text, font, max_width, draw):
        """Wraps text to fit within a given maximum width."""
        lines = []
        # Split by actual paragraphs first
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue

            words = paragraph.split(' ')
            current_line = []
            
            for word in words:
                test_line = " ".join(current_line + [word])
                try:
                    bbox = font.getbbox(test_line)
                    w = bbox[2] - bbox[0]
                except AttributeError:
                    w = draw.textlength(test_line, font=font)
                
                if w <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        # Single word is too long (very rare), just append it
                        lines.append(word)
                        current_line = []
            
            if current_line:
                lines.append(" ".join(current_line))
                
        return lines

    def generate_wiki_page(self):
        """
        Generates the final image with the Wikipedia article fitting into margins.

        Returns:
            PIL.Image: The generated wikipedia page.
        """
        title, extract, article_url = self._fetch_random_article()

        # 1. Create a base white image
        img = Image.new("L", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)

        # 2. Select fonts
        font_names = ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "FreeSansBold.ttf", "LiberationSans-Bold.ttf"]
        
        font_large = font_medium = font_small = None
        for font_name in font_names:
            try:
                font_large = ImageFont.truetype(font_name, 50)
                font_medium = ImageFont.truetype(font_name, 30)
                font_small = ImageFont.truetype(font_name, 22)
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

        # Margins and layout
        margin_x = 80
        y_offset = 120
        max_text_width = self.width - (margin_x * 2)

        # 3. Draw Title (Wrapped if necessary)
        header_text = f"Náhodná Wikipedie: {title}" if self.lang == "cs" else f"Random Wikipedia: {title}"
        title_lines = self._wrap_text(header_text, font_large, max_text_width, draw)
        
        for line in title_lines:
            try:
                bbox = font_large.getbbox(line)
                text_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
            except AttributeError:
                text_width = draw.textlength(line, font=font_large)
                line_height = 50 # approximation
            
            x = (self.width - text_width) // 2
            draw.text((x, y_offset), line, font=font_large, fill=0)
            y_offset += line_height + 15
        
        y_offset += 60 # extra space below title

        # 4. Reserve space for the link at the very bottom
        link_text = f"Celý článek: {article_url}" if self.lang == "cs" else f"Full article: {article_url}"
        link_y_start = self.height - 100

        # Draw the link at the bottom
        try:
            bbox_link = font_small.getbbox(link_text)
            link_width = bbox_link[2] - bbox_link[0]
        except AttributeError:
            link_width = draw.textlength(link_text, font=font_small)
        
        x_link = (self.width - link_width) // 2
        draw.text((x_link, link_y_start), link_text, font=font_small, fill=0)

        # 5. Draw Extract text until we run out of vertical space
        content_lines = self._wrap_text(extract, font_medium, max_text_width, draw)
        
        for line in content_lines:
            if not line:
                y_offset += 15 # Paragraph spacing
                continue

            try:
                bbox = font_medium.getbbox(line)
                line_height = bbox[3] - bbox[1]
            except AttributeError:
                line_height = 30 # approximation

            if y_offset + line_height + 40 > link_y_start: # 40px buffer padding
                break # Stop drawing if we reach our reserved lowest point

            draw.text((margin_x, y_offset), line, font=font_medium, fill=0)
            y_offset += line_height + 10 # Line spacing

        return img

if __name__ == "__main__":
    generator_en = WikiPageGenerator(lang="en")
    img_en = generator_en.generate_wiki_page()
    img_en.save("test_wiki_page_en.png")
    print("Test page generated as test_wiki_page_en.png")
    
    generator_cs = WikiPageGenerator(lang="cs")
    img_cs = generator_cs.generate_wiki_page()
    img_cs.save("test_wiki_page_cs.png")
    print("Test page generated as test_wiki_page_cs.png")
