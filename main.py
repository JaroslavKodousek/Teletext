import requests
import os
from PIL import Image, ImageOps, ImageDraw, ImageFont  # <-- Add ImageDraw, ImageFont import
from io import BytesIO
from datetime import datetime
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def download_teletext_images_and_create_pdf(start_page=100, end_page=170, channel="CT2"):
    """
    Downloads teletext page images from the Czech Television API for a specified channel and page range,
    saves non-uniform images to a timestamped folder, and creates a PDF containing all valid images.
    Args:
        start_page (int, optional): The starting teletext page number (inclusive). Defaults to 100.
        end_page (int, optional): The ending teletext page number (exclusive). Defaults to 170.
        channel (str, optional): The teletext channel to download from (e.g., "CT2"). Defaults to "CT2".
    Returns:
        str or None: The file path to the created PDF if images were saved, otherwise None.
    Side Effects:
        - Creates a timestamped folder under "data" containing downloaded images and the resulting PDF.
        - Prints status messages for skipped uniform images, failed downloads, and PDF creation.
    """

    if not os.path.isdir("data"):
        os.makedirs("data")
    # Create a new folder with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = os.path.join("data", f"{timestamp}_teletext")
    os.makedirs(folder_name, exist_ok=True)
    folder_name_images = os.path.join(folder_name, "images")
    os.makedirs(folder_name_images, exist_ok=True)

    saved_images = []

    for page in range(start_page, end_page):
        url = f"https://api-teletext.ceskatelevize.cz/services-old/teletext/picture.php?channel={channel}&page={page}"
        response = requests.get(url)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            # Convert to grayscale
            img = img.convert("L")
            # Apply extreme contrast (binarization)
            threshold = 128
            img = img.point(lambda p: 255 if p > threshold else 0)
            # Invert colors for better readability on eBook readers
            img = ImageOps.invert(img)
            pixels = img.getdata()
            first_pixel = pixels[0]
            if all(pixel == first_pixel for pixel in pixels):
                print(f"Skipped uniform color image for page {page}")
            else:
                # Add extra space at the bottom for the page number
                extra_height = 20  # Height for the page number area
                new_img = Image.new("L", (img.width, img.height + extra_height), 255)  # White background
                new_img.paste(img, (0, 0))
                draw = ImageDraw.Draw(new_img)
                try:
                    font = ImageFont.truetype("arial.ttf", 12)  # Tiny font
                except:
                    font = ImageFont.load_default()
                text = f"Page {page}"
                bbox = font.getbbox(text)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = (new_img.width - text_width) // 2
                y = img.height + (extra_height - text_height) // 2
                draw.text((x, y), text, font=font, fill=0)  # Black text
                img_path = os.path.join(folder_name_images, f"teletext_{page}.png")
                new_img.save(img_path, format="PNG")
                saved_images.append(img_path)
        else:
            print(f"Failed to retrieve page {page}: {response.status_code}")

    # Create a PDF with all saved images
    date_str = datetime.now().strftime("%d.%m.%Y")
    pdf_filename = f"Teletext {date_str}.pdf"
    pdf_path = os.path.join(folder_name, pdf_filename)
    if saved_images:
        image_objs = [Image.open(img_path).convert("RGB") for img_path in saved_images]
        image_objs[0].save(pdf_path, save_all=True, append_images=image_objs[1:])
        print(f"PDF created at {pdf_path}")
        return pdf_path
    else:
        print("No images saved, PDF not created.")
        return None

def send_pdf_via_email(pdf_path, sender_email, sender_password, recipient_email, subject="Teletext PDF", body="Please find the attached PDF."):
    """
    Sends a PDF file as an email attachment using SMTP over SSL.
    Args:
        pdf_path (str): Path to the PDF file to be sent.
        sender_email (str): Email address of the sender.
        sender_password (str): Password for the sender's email account.
        recipient_email (str): Email address of the recipient.
        subject (str, optional): Subject of the email. Defaults to "Teletext PDF".
        body (str, optional): Body text of the email. Defaults to "Please find the attached PDF.".
    Raises:
        ValueError: If sender_email or sender_password is not provided.
    Side Effects:
        Sends an email with the specified PDF attachment to the recipient.
        Prints a confirmation message upon successful sending.
    """
    
    if not sender_email or not sender_password:
        raise ValueError("Sender email or password not set in environment variables.")

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))

    with smtplib.SMTP_SSL("smtp.seznam.cz", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)
        print(f"Email sent to {recipient_email} with attachment {pdf_path}")

def main(sender_email, sender_password, recipient_email):
        output_path = download_teletext_images_and_create_pdf()
        if output_path:
            send_pdf_via_email(output_path, sender_email, sender_password, recipient_email)
    
if __name__ == "__main__":
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    if not sender_email or not sender_password or not recipient_email:
        raise ValueError("Email credentials or recipient email not set in environment variables.")
    else:
        main(sender_email, sender_password, recipient_email)