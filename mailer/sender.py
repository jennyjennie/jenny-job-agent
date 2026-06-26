import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import Settings


def send_email(
    to: str,
    subject: str,
    html: str,
    text: str,
    settings: Settings,
) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.email_from, to, msg.as_string())
        print(f"[Email] Sent to {to}")
        return True
    except smtplib.SMTPException as e:
        print(f"[Email] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[Email] Unexpected error: {e}")
        return False
