import os
import json
from bcolors import bcolors
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


"""
Notification module.

The "Golden Rules":
 * No more than 1 email can be sent per day
 * No Crew gets emailed to everyone (no more than once per day)

 Note: Add exports for YAHOO_EMAIL and YAHOO_PASSWORD to the venv/bin/activate script
"""

class Notifier :

    def __init__(self, log_status_path, contacts_by_squad_map):
        self.log_status_path = log_status_path
        self.contacts_by_squad_map = contacts_by_squad_map
        self.yahoo_email = os.environ['YAHOO_EMAIL']
        self.yahoo_password = os.environ['YAHOO_PASSWORD']


    def get_email_log_dir_name(self, send_date):
        return f'{self.log_status_path}/{send_date}'


    def should_send_email(self, today, squad):
        send_date = today.strftime('%Y%m%d')
        log_dir_name = self.get_email_log_dir_name(send_date, squad)
        file_name = f'{log_dir_name}/email_log_{squad}.json'
        return not os.path.exists(file_name)
        

    def log_sent_email(self, squad, send_date, subject, body, recipients):
        log_dir_name = self.get_email_log_dir_name(send_date)
        log_filename = f'{log_dir_name}/email_log_{squad}.json'
        os.makedirs(log_dir_name, exist_ok=True)

        email_log = {
            'squad': squad,
            'subject': subject,
            'body': body,
            'recipients': recipients
        }

        with open(log_filename, 'w') as writer:
            json.dump(email_log, writer)

        print(f'Saved email log file: {bcolors.OKGREEN}{log_filename}{bcolors.ENDC}')


    def send_email2(self, subject, body, to_email, cc_email=None):
        conn = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) 
        conn.ehlo()
        conn.login(self.yahoo_email, self.yahoo_password)
        conn.sendmail(self.yahoo_email, to_email, body)
        conn.quit()        


    def send_email(self, subject, body_text, body_html, to_email, cc_email=None, bcc_email=None):
        # Set up the MIME
        message = MIMEMultipart('alternative')
        message['From'] = f'Somerset County EMS Collaborative <{self.yahoo_email}>'
        message['To'] = to_email
        if cc_email is not None:
            message['Cc'] = cc_email
        if bcc_email is not None:
            message['Bcc'] = bcc_email

        message['Subject'] = subject

        cc_email = '' if cc_email is None else cc_email
        bcc_email = '' if bcc_email is None else bcc_email

        # Attach the body to the email
        # message.attach(MIMEText(body, 'plain'))

        # Connect to Yahoo's SMTP server
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as server:

            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')

            message.attach(part1)
            message.attach(part2)
            
            # Login to your Yahoo account
            server.login(self.yahoo_email, self.yahoo_password)

            recipients = to_email.split(',') + cc_email.split(',') + bcc_email.split(',')
            
            # Send the email
            server.sendmail(self.yahoo_email, recipients, message.as_string())


# Example usage
if __name__ == "__main__":
    subject = "Test Email"
    body = "This is a test email sent from Python."
    to_email = "gnowakowski@gmail.com"
    cc_email = None
    bcc_email = 'gmn314@yahoo.com'
    # cc_email = "gmn314@yahoo.com"
    html_body = """
    <html>
        <head></head>
        <body>
            <p>Hi!<br>
                How are you?<br>
            </p>
        </body>
    </html>
    """

    notifier = Notifier('', None)

    notifier.send_email(subject, body, html_body, to_email, cc_email, bcc_email)


