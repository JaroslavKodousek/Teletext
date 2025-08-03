import requests
import os
from PIL import Image
from io import BytesIO
from datetime import datetime
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def download_teletext_images_and_create_pdf(start_page=100, end_page=170, channel="CT2"):
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
            pixels = img.getdata()
            first_pixel = pixels[0]
            if all(pixel == first_pixel for pixel in pixels):
                print(f"Skipped uniform color image for page {page}")
            else:
                img_path = os.path.join(folder_name_images, f"teletext_{page}.png")
                with open(img_path, "wb") as f:
                    f.write(response.content)
                saved_images.append(img_path)
        else:
            print(f"Failed to retrieve page {page}: {response.status_code}")

    # Create a PDF with all saved images
    pdf_path = os.path.join(folder_name, f"{timestamp}_teletext.pdf")
    if saved_images:
        image_objs = [Image.open(img_path).convert("RGB") for img_path in saved_images]
        image_objs[0].save(pdf_path, save_all=True, append_images=image_objs[1:])
        print(f"PDF created at {pdf_path}")
        return pdf_path
    else:
        print("No images saved, PDF not created.")
        return None

def send_pdf_via_email(pdf_path, sender_email, sender_password, recipient_email, subject="Teletext PDF", body="Please find the attached PDF."):
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