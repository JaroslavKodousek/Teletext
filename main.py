import requests
import os
from PIL import (
    Image,
    ImageOps,
    ImageDraw,
    ImageFont,
)  # <-- Add ImageDraw, ImageFont import
from io import BytesIO
from datetime import datetime
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FirstPageGenerator:
    """Generates a greeting first page for the PDF."""

    def __init__(self, greeting_text="Ahoj, zdravím tě!", width=800, height=600):
        self.greeting_text = greeting_text
        self.width = width
        self.height = height

    def generate_first_page(self):
        """
        Generates a first page image with greeting text.

        Returns:
            PIL.Image: The generated first page image.
        """
        img = Image.new("L", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()

        bbox = font.getbbox(self.greeting_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        draw.text((x, y), self.greeting_text, font=font, fill=0)
        return img


class DownloadTeletext:
    """Handles downloading and processing teletext images."""

    API_URL = "https://api-teletext.ceskatelevize.cz/services-old/teletext/picture.php"

    def __init__(self, start_page=100, end_page=170, channel="CT2"):
        self.start_page = start_page
        self.end_page = end_page
        self.channel = channel
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
        """Downloads and processes teletext images."""
        for page in range(self.start_page, self.end_page):
            self._download_single_page(page, folder_name_images)

    def _download_single_page(self, page, folder_name_images):
        """Downloads and processes a single teletext page."""
        url = f"{self.API_URL}?channel={self.channel}&page={page}"
        response = requests.get(url)

        if response.status_code == 200:
            self._process_image(response.content, page, folder_name_images)
        else:
            print(f"Failed to retrieve page {page}: {response.status_code}")

    def _process_image(self, image_data, page, folder_name_images):
        """Processes a downloaded image and saves it if it's not uniform."""
        img = Image.open(BytesIO(image_data))
        img = img.convert("L")

        # Apply binarization
        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0)
        img = ImageOps.invert(img)

        # Check if image is uniform
        pixels = img.get_flattened_data()
        if all(pixel == pixels[0] for pixel in pixels):
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

        if self.saved_images:
            # Generate first page with greeting
            first_page_gen = FirstPageGenerator()
            first_page = first_page_gen.generate_first_page().convert("RGB")

            # Combine first page with downloaded images
            image_objs = [first_page] + [
                Image.open(img_path).convert("RGB") for img_path in self.saved_images
            ]
            image_objs[0].save(pdf_path, save_all=True, append_images=image_objs[1:])
            print(f"PDF created at {pdf_path}")
            self.pdf_path = pdf_path
            return pdf_path
        else:
            print("No images saved, PDF not created.")
            return None


class EmailSender:
    """Handles sending emails with PDF attachments."""

    SMTP_SERVER = "smtp.seznam.cz"
    SMTP_PORT = 465

    def __init__(self, sender_email, sender_password, dry_run=False):
        if not dry_run and (not sender_email or not sender_password):
            raise ValueError(
                "Sender email or password not set in environment variables."
            )
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.dry_run = dry_run

    def send_pdf(
        self,
        pdf_path,
        recipient_email,
        subject="Teletext PDF",
        body="Please find the attached PDF.",
    ):
        """
        Sends a PDF file as an email attachment using SMTP over SSL.

        Args:
            pdf_path (str): Path to the PDF file to be sent.
            recipient_email (str): Email address of the recipient.
            subject (str, optional): Subject of the email. Defaults to "Teletext PDF".
            body (str, optional): Body text of the email. Defaults to "Please find the attached PDF.".
        """
        if self.dry_run:
            print(
                f"[DRY RUN] Email would be sent to {recipient_email} with attachment {pdf_path}"
            )
            return

        msg = EmailMessage()
        msg["From"] = self.sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(body)

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            msg.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(pdf_path),
            )

        with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as smtp:
            smtp.login(self.sender_email, self.sender_password)
            smtp.send_message(msg)
            print(f"Email sent to {recipient_email} with attachment {pdf_path}")


def main(sender_email, sender_password, recipient_email, dry_run=False):
    """
    Main function to download teletext and send via email.

    Args:
        sender_email (str): Email address of the sender.
        sender_password (str): Password for the sender's email account.
        recipient_email (str): Email address of the recipient.
        dry_run (bool, optional): If True, skips sending the email. Defaults to False.
    """
    # Download teletext images and create PDF
    downloader = DownloadTeletext()
    pdf_path = downloader.download_and_create_pdf()

    # Send PDF via email if created successfully
    if pdf_path:
        email_sender = EmailSender(sender_email, sender_password, dry_run=dry_run)
        email_sender.send_pdf(pdf_path, recipient_email)


if __name__ == "__main__":
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    # Email credentials are only required if not in dry_run mode
    if not dry_run and (not sender_email or not sender_password or not recipient_email):
        raise ValueError(
            "Email credentials or recipient email not set in environment variables."
        )

    main(sender_email, sender_password, recipient_email, dry_run=dry_run)
