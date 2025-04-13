import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from logger import logger
from dotenv import load_dotenv;load_dotenv()


sender_mail = os.getenv("P_SENDER_MAIL")
password = os.getenv("P_PASSWORD")
receiver_mail = os.getenv("P_RECEIVER_MAIL")
title = "Raspberry Pi Bitcoin Price Indicator"


def send_email(msg):
    try:
        # Create the email
        message = MIMEMultipart()
        message['From'] = sender_mail
        message['To'] = receiver_mail
        message['Subject'] = title

        # Attach the email content
        message.attach(MIMEText(msg, 'plain'))

        # Connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(sender_mail, password)
            s.sendmail(sender_mail, receiver_mail, message.as_string())

        logger.info("Email sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    # Test the email sending function
    if send_email("Test email from Raspberry Pi"):
        print("Email sent successfully")
    else:
        print("Failed to send email")