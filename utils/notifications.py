import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

#discord bot on server de moi
def send_discord_notification(report):
    """
    Send a Discord notification based on the report.
    Args:
        report (dict): Contains 'report' (str) and 'has_strikes' (bool)
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ Discord webhook URL not configured.")
        return False

    if not report.get('has_strikes', False):
        print("✅ No strikes detected. Discord notification skipped.")
        return True

    try:
        payload = {
            "content": f"🚨 **Strike Alert:**\n{report['report']}"
        }
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ Discord notification sent successfully.")
            return True
        else:
            print(f"❌ Failed to send Discord notification. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending Discord notification: {e}")
        return False

#email notif
def send_email_notification(subject, body):
    email_host = os.getenv("EMAIL_HOST")
    email_port = int(os.getenv("EMAIL_PORT", 587))
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    if not all([email_host, email_port, email_username, email_password, email_receiver]):
        print("❌ Email configuration is incomplete.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = email_username
        msg['To'] = email_receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            server.sendmail(email_username, email_receiver, msg.as_string())

        print("✅ Email notification sent successfully.")
        return True

    except Exception as e:
        print(f"❌ Error sending email notification: {e}")
        return False
