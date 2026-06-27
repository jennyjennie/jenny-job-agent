import smtplib
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config.settings import Settings


def send_email(
    to: str,
    subject: str,
    html: str,
    text: str,
    settings: Settings,
    attachments: list[str] | None = None,
) -> bool:
    print(f"[Email] Preparing to send → {to}")
    print(f"[Email] Subject : {subject}")
    print(f"[Email] From    : {settings.email_from}")
    print(f"[Email] GMAIL_USER set       : {bool(settings.gmail_user)}")
    print(f"[Email] GMAIL_APP_PASSWORD set: {bool(settings.gmail_app_password)}")
    if attachments:
        print(f"[Email] Attachments ({len(attachments)}): {[Path(p).name for p in attachments]}")

    if not settings.gmail_user or not settings.gmail_app_password:
        print("[Email] ERROR: GMAIL_USER or GMAIL_APP_PASSWORD is empty — cannot send.")
        print("[Email] Set them in your .env file (copy from .env.example).")
        return False

    # When attachments present, wrap text+html in multipart/alternative inside multipart/mixed
    if attachments:
        msg = MIMEMultipart("mixed")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(text, "plain", "utf-8"))
        alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)

        for path in attachments:
            p = Path(path)
            if not p.exists():
                print(f"[Email] Attachment not found, skipping: {path}")
                continue
            part = MIMEBase(
                "application",
                "vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            part.set_payload(p.read_bytes())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=p.name)
            msg.attach(part)
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to

    print("[Email] Connecting to smtp.gmail.com:465 ...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("[Email] Connected. Logging in ...")
            server.login(settings.gmail_user, settings.gmail_app_password)
            print("[Email] Login OK. Sending ...")
            server.sendmail(settings.email_from, to, msg.as_string())
        print(f"[Email] ✓ Sent successfully to {to}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[Email] SMTP auth failed (wrong App Password or 2FA not enabled): {e}")
        print("[Email] → Go to myaccount.google.com/apppasswords to generate a 16-char App Password")
        return False
    except smtplib.SMTPException as e:
        print(f"[Email] SMTP error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[Email] Unexpected error: {e}")
        traceback.print_exc()
        return False
