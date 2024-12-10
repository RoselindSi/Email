# email_tool.py  // Asynchronous Gmail Email Sending Tool Class
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncGmailTool:
    """
    Asynchronous Gmail Email Sending Tool Class

    This class provides the functionality to send emails asynchronously through Gmail's SMTP server.
    It supports the following features:
    - Asynchronous email sending
    - HTML format content
    - Multiple recipients
    - File attachments
    - Automatic TLS encryption

    Usage example:
        gmail_tool = AsyncGmailTool(
            smtp_username="your-email@gmail.com",
            smtp_password="your-app-password"  # Obtain by logging into Gmail
        )
        await gmail_tool.send_email(
            to_emails=["recipient@example.com"],
            subject="Test Email",
            body="Email content"
        )
    """

    def __init__(
        self,
        smtp_username: str,
        smtp_password: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587
    ):
        """
        Initialize the Gmail Email Tool

        Args:
            smtp_username: Gmail email address, used as the sender's address
            smtp_password: Gmail app-specific password, generated in Gmail's security settings
                           Note: This is not the Gmail account login password
            smtp_server: SMTP server address, default is Gmail's SMTP server
            smtp_port: SMTP server port, default is 587 (TLS)
                      Gmail also supports port 465 (SSL)

        Note:
            To use Gmail's SMTP service, you need:
            1. Enable Gmail's two-factor authentication
            2. Generate an app-specific password
            3. Ensure SMTP port is not blocked by firewall
        """
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """
        Core method for asynchronously sending emails

        Args:
            to_emails: List of recipient email addresses, supports multiple recipients
            subject: Email subject
            body: Email body content
            html: Whether to treat the body as HTML content
                 True: The body will be sent in HTML format
                 False: The body will be sent in plain text format
            attachments: List of attachment file paths, each path should be a Path object
                       If no attachments are needed, pass None

        Returns:
            bool: Email sending result
                 True: Sending successful
                 False: Sending failed

        Raises:
            Will not throw exceptions, all exceptions are caught and logged
        """
        try:
            # Create a multipart email container
            message = MIMEMultipart()
            message["From"] = self.smtp_username
            message["To"] = ", ".join(to_emails)  # Separate multiple recipients with commas
            message["Subject"] = subject

            # Set the email body
            # Decide content type based on html parameter: html or plain
            content_type = "html" if html else "plain"
            message.attach(MIMEText(body, content_type, "utf-8"))

            # Handle attachments (if any)
            if attachments:
                for attachment_path in attachments:
                    # Read attachment file
                    with open(attachment_path, "rb") as f:
                        # Create attachment object
                        attachment = MIMEApplication(f.read())
                        # Set attachment header, specifying filename
                        attachment.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=attachment_path.name
                        )
                        message.attach(attachment)

            # Connect to SMTP server using an asynchronous context manager
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=True  # Enable TLS encryption
            ) as smtp:
                # Login to SMTP server
                await smtp.login(self.smtp_username, self.smtp_password)
                # Send email
                await smtp.send_message(message)

            # Log success
            logger.info(f"Email successfully sent to {', '.join(to_emails)}")
            return True

        except Exception as e:
            # Log error
            logger.error(f"Error occurred while sending email: {str(e)}")
            return False
