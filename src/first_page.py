import datetime
import json
import urllib.request

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


class FirstPageGenerator:
    """Generates a greeting first page for the PDF."""

    def __init__(self, greeting_text="Ahoj!", width=1072, height=1448):
        self.greeting_text = greeting_text
        self.width = width
        self.height = height

    def _fetch_weather(self):
        """Fetches weather forecast for Prague using OpenMeteo API."""
        url = "https://api.open-meteo.com/v1/forecast?latitude=50.1044903&longitude=14.3913725&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Europe%2FBerlin&forecast_days=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read())
                return data.get('daily', {})
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

    def _fetch_namesdays(self):
        """Fetches namesdays for next 3 days using SvatkyAPI.cz."""
        days = []
        base_date = datetime.date.today()
        for i in range(3):
            target_date = base_date + datetime.timedelta(days=i)
            url = f"https://svatkyapi.cz/api/day/{target_date.year}-{target_date.month:02d}-{target_date.day:02d}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as res:
                    data = json.loads(res.read())
                    days.append(data.get('name', 'Neznámý'))
            except Exception as e:
                print(f"Error fetching namesday: {e}")
                days.append('Chyba')
        return days

    def _fetch_btc_price(self):
        """Fetches current Bitcoin price in USD and 3-day trend from Yahoo Finance."""
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?range=5d&interval=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read())
                closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
                valid_closes = [c for c in closes if c is not None]
                if len(valid_closes) >= 4:
                    price_3d_ago = float(valid_closes[-4])
                else:
                    price_3d_ago = float(valid_closes[0]) if valid_closes else 0.0
                
                regular_price = float(data['chart']['result'][0]['meta']['regularMarketPrice'])
                
                if price_3d_ago:
                    trend = "↑" if regular_price > price_3d_ago else "↓" if regular_price < price_3d_ago else "→"
                else:
                    trend = ""
                return regular_price, trend
        except Exception as e:
            print(f"Error fetching BTC: {e}")
            return None, ""
    def _fetch_eunl_price(self):
        """Fetches current EUNL ETF price in EUR and 3-day trend from Yahoo Finance."""
        url = "https://query1.finance.yahoo.com/v8/finance/chart/EUNL.DE?range=1mo&interval=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read())
                closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
                valid_closes = [c for c in closes if c is not None]
                if len(valid_closes) >= 4:
                    current_price = float(valid_closes[-1])
                    price_3d_ago = float(valid_closes[-4])
                    trend = "↑" if current_price > price_3d_ago else "↓" if current_price < price_3d_ago else "→"
                else:
                    current_price = float(valid_closes[-1]) if valid_closes else 0.0
                    trend = ""
                
                exact_price_url = "https://query1.finance.yahoo.com/v8/finance/chart/EUNL.DE"
                req_ext = urllib.request.Request(exact_price_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req_ext) as res_ext:
                    data_ext = json.loads(res_ext.read())
                    regular_price = float(data_ext['chart']['result'][0]['meta']['regularMarketPrice'])
                    if len(valid_closes) >= 4:
                        trend = "↑" if regular_price > price_3d_ago else "↓" if regular_price < price_3d_ago else "→"
                    return regular_price, trend
        except Exception as e:
            print(f"Error fetching EUNL: {e}")
            return None, ""

    def _fetch_exchange_rates(self):
        """Fetches current CZK/EUR and CZK/PLN exchange rates from CNB."""
        url = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
        rates = {"EUR": None, "PLN": None}
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as res:
                lines = res.read().decode('utf-8').split('\n')
                for line in lines:
                    if '|EUR|' in line:
                        rates['EUR'] = float(line.split('|')[-1].replace(',', '.'))
                    elif '|PLN|' in line:
                        rates['PLN'] = float(line.split('|')[-1].replace(',', '.'))
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
        return rates
    def _get_wmo_description(self, code):
        """Map simple WMO weather codes to Czech descriptions."""
        if code == 0: return "Jasno"
        if code in [1, 2, 3]: return "Oblačno"
        if code in [45, 48]: return "Mlha"
        if code in [51, 53, 55, 56, 57]: return "Mrholí"
        if code in [61, 63, 65, 66, 67]: return "Déšť"
        if code in [71, 73, 75, 77]: return "Sněží"
        if code in [80, 81, 82]: return "Přeháňky"
        if code in [85, 86]: return "Sněžení"
        if code in [95, 96, 99]: return "Bouřka"
        return "Neznámé"

    def generate_first_page(self):
        """
        Generates a first page image with greeting text, weather, and namesdays.

        Returns:
            PIL.Image: The generated first page image.
        """
        img = Image.new("L", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)

        # Try finding a bold font for better Kindle readability
        font_names = ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "FreeSansBold.ttf", "LiberationSans-Bold.ttf"]
        
        font_large = font_medium = font_small = font_tiny = None
        
        for font_name in font_names:
            try:
                font_large = ImageFont.truetype(font_name, 60)
                font_medium = ImageFont.truetype(font_name, 46)
                font_small = ImageFont.truetype(font_name, 36)
                font_tiny = ImageFont.truetype(font_name, 28)
                break
            except OSError:
                continue

        if font_large is None:
            try:
                font_large = ImageFont.load_default(size=60)
                font_medium = ImageFont.load_default(size=46)
                font_small = ImageFont.load_default(size=36)
                font_tiny = ImageFont.load_default(size=28)
            except TypeError:
                font_large = font_medium = font_small = font_tiny = ImageFont.load_default()

        today = datetime.date.today()
        weather = self._fetch_weather()
        namesdays = self._fetch_namesdays()

        y_offset = 120

        # Header - Greeting and Date
        cz_days = ["pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle"]
        cz_short_days = ["PO", "ÚT", "ST", "ČT", "PÁ", "SO", "NE"]
        day_of_week = cz_days[today.weekday()]
        header_text = f"{self.greeting_text} Dnes je {day_of_week} {today.strftime('%d.%m.%Y')}."
        try:
            bbox = font_large.getbbox(header_text)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width = draw.textlength(header_text, font=font_large)

        x = (self.width - text_width) // 2
        draw.text((x, y_offset), header_text, font=font_large, fill=0)
        y_offset += 190

        # Weather Section
        draw.text((60, y_offset), "Počasí v Praze (na 3 dny):", font=font_large, fill=0)
        y_offset += 110
        if weather and 'time' in weather:
            for i in range(3):
                date_str = weather['time'][i]
                # Convert YYYY-MM-DD to DD.MM.YYYY
                date_parsed = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                date_formatted = date_parsed.strftime("%d.%m.%Y")
                day_abbr = cz_short_days[date_parsed.weekday()]
                
                t_max = weather['temperature_2m_max'][i]
                t_min = weather['temperature_2m_min'][i]
                w_code = weather['weather_code'][i]
                desc = self._get_wmo_description(w_code)
                
                text = f"{day_abbr}: Min {t_min}°C, Max {t_max}°C, {desc}"
                draw.text((80, y_offset), text, font=font_medium, fill=0)
                y_offset += 80
        else:
            draw.text((80, y_offset), "Nepodařilo se načíst data o počasí.", font=font_medium, fill=0)
            y_offset += 80

        y_offset += 140

        # Namesdays and Markets Section
        draw.text((60, y_offset), "Svátek:", font=font_large, fill=0)
        draw.text((600, y_offset), "Trhy:", font=font_large, fill=0) # Same size as Svátek slaví
        
        y_left = y_offset + 110
        y_right = y_offset + 110 # Adjusted to bring items a bit closer to header

        market_texts = []
        currency_texts = []
        btc_price, btc_trend = self._fetch_btc_price()
        eunl_price, eunl_trend = self._fetch_eunl_price()
        exchange_rates = self._fetch_exchange_rates()
        
        if btc_price:
            market_texts.append(f"BTC: {btc_price:,.2f} USD {btc_trend}".replace(',', ' '))
        else:
            market_texts.append("BTC: Neznámé")
            
        if eunl_price:
            market_texts.append(f"EUNL: {eunl_price:.2f} EUR {eunl_trend}")
        else:
            market_texts.append("EUNL: Neznámé")
            
        if exchange_rates.get('EUR'):
            currency_texts.append(f"EUR/CZK: {exchange_rates['EUR']:.2f} CZK")
        else:
            currency_texts.append("EUR/CZK: Neznámé")
            
        if exchange_rates.get('PLN'):
            currency_texts.append(f"PLN/CZK: {exchange_rates['PLN']:.2f} CZK")
        else:
            currency_texts.append("PLN/CZK: Neznámé")

        # Draw left column (Namesdays)
        for i in range(3):
            target_date = today + datetime.timedelta(days=i)
            day_abbr = cz_short_days[target_date.weekday()]
            label = "Dnes" if i == 0 else "Zítra" if i == 1 else "Pozítří"
            text_nd = f"{label} ({day_abbr}): {namesdays[i]}"
            draw.text((80, y_left), text_nd, font=font_small, fill=0)
            y_left += 80

        # Draw right column (Markets)
        for text in market_texts:
            draw.text((620, y_right), text, font=font_small, fill=0)
            y_right += 70
            
        # Draw right column (Currencies)
        y_right += 50 # Added more space between blocks
        draw.text((600, y_right), "Měny:", font=font_large, fill=0)
        y_right += 110
        for text in currency_texts:
            draw.text((620, y_right), text, font=font_small, fill=0)
            y_right += 70

        return img

if __name__ == "__main__":
    generator = FirstPageGenerator()
    img = generator.generate_first_page()
    img.save("test_first_page.png")
    print("Test page generated as test_first_page.png")
