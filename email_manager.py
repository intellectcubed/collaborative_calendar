import csv
from datetime import datetime
import os
from bcolors import bcolors
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

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
        return f"{self.log_status_path}/{send_date.strftime('%Y%m%d')}"
    
    def get_checksum(self, email_body):
        """This function returns the checksum of a file."""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(email_body.encode('utf-8'))
        return sha256_hash.hexdigest()    


    def get_email_log(self, send_date):
        log_dir_name = self.get_email_log_dir_name(send_date)
        file_name = f'{log_dir_name}/email_log.csv'
        if not os.path.exists(file_name):
            return None

        log = []        
        with open(file_name, 'r') as reader:
            sent_reader = csv.reader(reader, delimiter='|')
            for line in sent_reader:
                log.append(line)

        return log 


    def should_send_email(self, send_date, checksum):
        log_dir_name = self.get_email_log_dir_name(send_date)
        file_name = f'{log_dir_name}/email_log.csv'
        if not os.path.exists(file_name):
            return True
        
        with open(file_name, 'r') as reader:
            sent_reader = csv.reader(reader, delimiter='|')
            for line in sent_reader:
                if line[0].strip() == checksum:
                    return False

        return True 
            

    def log_sent_email(self, date, to_email, cc_email, bcc_email, checksum):
        log_dir_name = self.get_email_log_dir_name(date)
        os.makedirs(log_dir_name, exist_ok=True)
        file_name = f'{log_dir_name}/email_log.csv'
        with open(file_name, 'a') as writer:
            csv_writer = csv.writer(writer, delimiter='|')
            csv_writer.writerow([checksum, to_email, cc_email, bcc_email])


    def send_email(self, subject, body_text, body_html, to_email, cc_email=None, bcc_email=None, dup_send_override=False):

        checksum = self.get_checksum(body_html)
        if not dup_send_override and not self.should_send_email(datetime.now(), checksum):
            print(f'{bcolors.WARNING}Email already sent today{bcolors.ENDC}')
            return

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

        self.log_sent_email(datetime.now(), to_email, cc_email, bcc_email, checksum)

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


