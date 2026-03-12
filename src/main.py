import os
from dotenv import load_dotenv

from src.downloader import DownloadTeletext
from src.email_sender import EmailSender

# Load environment variables from .env file
load_dotenv()


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


def cli():
    """Command-line entry point for the teletext project."""
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


if __name__ == "__main__":
    cli()
