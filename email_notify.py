import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = "joker696808@gmail.com"
EMAIL_PASSWORD = "psyl yqdx wnia gmnz"

def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        server.send_message(msg)
        server.quit()

        print("✅ Email sent!")
        return True

    except Exception as e:
        print("❌ Error:", e)
        return False