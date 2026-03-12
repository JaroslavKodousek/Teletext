import os
import smtplib
from email.message import EmailMessage


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
