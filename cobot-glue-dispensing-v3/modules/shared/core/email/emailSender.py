import base64
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
import os



logo_link = "https://www.plproject.net/wp-content/uploads/2025/07/long-logo-pl-project-newnew%D0%BD%D0%B5%D0%B2.png"

def image_to_base64(img_path: str) -> str:
    """Converts a local image to Base64 string for embedding in HTML."""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return encoded


def get_email_template(user_name: str, message: str, logo_url: str = logo_link):
    logo_html = f'<div class="header"><img src="{logo_url}" alt="Logo"></div>' if logo_url else ""

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>...</head>
    <body>
        <div class="container">
            {logo_html}
            <div class="content">
                <h2>Hello {user_name},</h2>
                <p>{message}</p>
            </div>
            <div class="footer">&copy; 2025 PL PROJECT LTD. All rights reserved.</div>
        </div>
    </body>
    </html>
    """
    return html_template

@dataclass
class EmailServiceConfig:
    smtp_server: str
    port: int
    username: str
    password: str

def get_default_email_config() -> EmailServiceConfig:
    return EmailServiceConfig(
        smtp_server="mail.plproject.net",
        port=465,
        username="ventsislav.iliev@plproject.net",
        password="L0)yN9l-NE5[")

class EmailSenderService:
    def __init__(self, config:EmailServiceConfig):
        """
        Initialize email sender service.
        :param smtp_server: SMTP server address
        :param port: SMTP port (465 for SSL)
        :param username: Full email address
        :param password: Password or app password
        """
        self.config = config
        self.smtp_server = config.smtp_server
        self.port = config.port
        self.username = config.username
        self.password = config.password

    def send_email(
        self,
        subject: str,
        body: str,
        to_emails: List[str],
        from_email: Optional[str] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ):
        from_email = from_email or self.username
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        # Attach the body
        msg.attach(MIMEText(body, "html" if html else "plain"))

        # Attach files
        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
                else:
                    print(f"⚠️ Attachment not found: {file_path}")

        # Connect to SMTP server using SSL
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.port) as server:
                server.login(self.username, self.password)
                server.sendmail(from_email, to_emails, msg.as_string())
                print(f"✅ Email sent to {to_emails}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            print("Check username/password or if the server requires an app password.")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            raise


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    sender = EmailSenderService(
        smtp_server="mail.plproject.net",
        port=465,
        username="ventsislav.iliev@plproject.net",
        password="L0)yN9l-NE5["  # Thunderbird password that works for sending
    )

    sender.send_email(
        subject="Python Test Email",
        body="<h2>Hello from Python!</h2><p>This is a test email.</p>",
        to_emails=["ventsislav.iliew@gmail.com"],
        html=True,
        attachments=[]  # ["path/to/file.pdf"] if needed
    )
