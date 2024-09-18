import smtplib
from jinja2 import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
# from weasyprint import HTML
# from io import BytesIO

SMPTP_SERVER_HOST = "localhost"
SMPTP_SERVER_PORT = 1025
SENDER_ADDRESS = "karthikreddy@gmail.com"
SENDER_PASSWORD = ''

def send_email(to_address, subject, message, attachment=None):
    msg=MIMEMultipart()
    msg["From"] = SENDER_ADDRESS 
    msg['To'] = to_address
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'html'))
    
    if attachment:
        part = MIMEBase('application', 'pdf')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="Monthly_report.pdf"')
        msg.attach(part)


    s =smtplib.SMTP(host=SMPTP_SERVER_HOST, port=SMPTP_SERVER_PORT)
    s.login(SENDER_ADDRESS,SENDER_PASSWORD)
    s.send_message(msg)
    s.quit()

    return "sent email succifuly"

# with open('templates\dailey_html_template.html') as file:
#     template = Template(file.read())
#     message = template.render()


    
