import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import EMAIL_USER, EMAIL_PASS, EMAIL_HOST, EMAIL_PORT

def send_invoice_email(to_email, subject, html_content):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email

        part = MIMEText(html_content, 'html')
        msg.attach(part)

        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"❌ Erreur Email : {e}")
        return False