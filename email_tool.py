# email_tool.py  // Asynchronous Gmail email sending utility class
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
import logging
from pathlib import Path
import ssl
import asyncio
from aiosmtplib.errors import SMTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncGmailTool:
    """
    Asynchronous Gmail email sending utility class
    
    This class provides the ability to send emails asynchronously through the Gmail SMTP server.
    Supports the following features:
    - Asynchronous email sending
    - HTML format content
    - Multiple recipients
    - File attachments
    - Automatic TLS encryption
    
    Usage example:
        gmail_tool = AsyncGmailTool(
            smtp_username="your-email@gmail.com",
            smtp_password="your-app-password"--obtain from Gmail login
        )
        await gmail_tool.send_email(
            to_emails=["recipient@example.com"],
            subject="Test Email",
            body="Email Content"
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
        Initialize Gmail email tool
        
        Args:
            smtp_username: Gmail email address, used as the sender's address
            smtp_password: Gmail app-specific password, generated in Gmail's security settings
                         Note: Not the Gmail account login password
            smtp_server: SMTP server address, default is Gmail's SMTP server
            smtp_port: SMTP server port, default is 587 (TLS)
                      Gmail also supports 465 (SSL) port
        
        Note:
            To use Gmail SMTP services, you need to:
            1. Enable Gmail's two-step verification
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
        Core method to send emails asynchronously
        
        Args:
            to_emails: List of recipient email addresses, supports multiple recipients
            subject: Email subject
            body: Email content
            html: Whether to treat the body as HTML content
                 True: The content will be sent in HTML format
                 False: The content will be sent in plain text format
            attachments: List of attachment file paths, each path should be a Path object
                       If no attachments are needed, pass None
        
        Returns:
            bool: Email sending result
                 True: Sending successful
                 False: Sending failed
        
        Raises:
            No exceptions will be thrown, all exceptions will be caught and logged
        """
        try:
            # Create a multipart email container
            message = MIMEMultipart()
            message["From"] = self.smtp_username
            message["To"] = ", ".join(to_emails)
            message["Subject"] = subject

            # Set the email body
            content_type = "html" if html else "plain"
            message.attach(MIMEText(body, content_type, "utf-8"))

            # Handle attachments (if any)
            if attachments:
                for attachment_path in attachments:
                    with open(attachment_path, "rb") as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=attachment_path.name
                        )
                        message.attach(attachment)

            # Create SSL context
            ssl_context = ssl.create_default_context()
            
            # Attempt to connect using SSL (port 465)
            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=465,  # Use SSL port
                use_tls=True,
                tls_context=ssl_context,
                timeout=30  # Set a timeout
            )

            try:
                logger.info("Starting SMTP connection...")
                await smtp.connect()
                
                logger.info(f"Logging in as {self.smtp_username}...")
                await smtp.login(self.smtp_username, self.smtp_password)
                logger.info("Starting to send email...")
                await smtp.send_message(message)
                logger.info("Email sent successfully")
                
                return True
                
            except SMTPException as smtp_error:
                logger.error(f"SMTP error: {str(smtp_error)}")
                # If SSL connection fails, try TLS connection (port 587)
                logger.info("Attempting TLS connection...")
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=587,
                    use_tls=False,
                    timeout=30
                )
                
                await smtp.connect()
                await smtp.starttls(tls_context=ssl_context)
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(message)
                
                return True
                
            except Exception as e:
                logger.error(f"Error during sending process: {str(e)}")
                return False
                
            finally:
                try:
                    await smtp.quit()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error while sending email: {str(e)}")
            return False