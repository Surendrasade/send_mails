import smtplib
import time
import random
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from email.message import EmailMessage

# --- CONFIGURATION FROM GITHUB SECRETS ---
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Paths must be relative to the GitHub repository root
RESUME_PATH = "SADE_SURENDRA_Resume_latest.docx" 
GOOGLE_SHEET_NAME = "recruiter_emails" 
DAILY_LIMIT = 100

def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Load Google Service Account JSON from GitHub Secrets
    google_creds_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not google_creds_str:
        raise ValueError("Google Credentials JSON not found in environment variables.")
        
    creds_dict = json.loads(google_creds_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(GOOGLE_SHEET_NAME).sheet1

def send_email(target_email):
    msg = EmailMessage()
    msg['Subject'] = "Job Application for DevOps Engineer Role || 5 Years of Exp || Immediate joiner"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = target_email

    body = """Hi Hiring Team, 

Greetings for the day!

I am SADE SURENDRA working as a DevOps Engineer for HCL TECH. I am writing this email regarding job availability for the DevOps Engineer role in your organization.

I have 4 years of IT experience. As per the requirement, I am forwarding my details along with my updated resume for your consideration. If you find my profile suitable for your requirement, please let me know.

Full Name : Sade Surendra
Total Experience : 4 years
Relevant Experience : 4 years
Current Company : HCL TECH
Current Location : Noida
Current CTC : 5 LPA
Expected CTC : As per the company standards
Notice period : IMMEDIATE

For any further information, please feel free to contact me.

Thanks & Regards,
Sade Surendra
sadesurendradevops@gmail.com
6281466869"""

    msg.set_content(body)

    # Attach the resume
    try:
        with open(RESUME_PATH, 'rb') as f:
            pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='P_SAIKUMAR_REDDY_Resume.pdf')
    except FileNotFoundError:
        print(f"Error: Could not find {RESUME_PATH}. Ensure it is committed to the repository.")
        raise

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

def process_emails():
    try:
        sheet = get_google_sheet()
        records = sheet.get_all_records()
    except Exception as e:
        print(f"Failed to connect to Google Sheets: {e}")
        return

    seen_emails = set()
    emails_sent_today = 0

    # Step 1: Build the memory bank of previously sent emails
    for row in records:
        if str(row.get('status', '')).strip().lower() == 'sent':
            seen_emails.add(str(row.get('email', '')).strip().lower())

    # Step 2: Process Pending rows
    for index, row in enumerate(records):
        try:
            status_col_index = list(row.keys()).index('status') + 1 
        except ValueError:
            print("Error: Could not find 'status' column. Check your sheet headers.")
            return

        gsheet_row = index + 2 
        
        email_clean = str(row.get('email', '')).strip().lower()
        current_status = str(row.get('status', '')).strip().lower()

        if not email_clean:
            continue

        if current_status == 'pending':
            
            # --- DUPLICATE CHECK ---
            if email_clean in seen_emails:
                print(f"Skipping duplicate: {email_clean}")
                sheet.update_cell(gsheet_row, status_col_index, 'duplicate')
                continue
            
            # --- DAILY LIMIT CHECK ---
            if emails_sent_today >= DAILY_LIMIT:
                print("Daily limit reached. Stopping for today.")
                break
                
            try:
                print(f"Sending to {email_clean}...")
                send_email(email_clean)
                
                # Update GSheet instantly
                sheet.update_cell(gsheet_row, status_col_index, 'sent')
                seen_emails.add(email_clean)
                emails_sent_today += 1
                
                # Sleep to mimic human sending
                sleep_time = random.randint(30, 90)
                print(f"Success! Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Failed to send to {email_clean}. Error: {e}")
                sheet.update_cell(gsheet_row, status_col_index, 'failed')

    print(f"Job complete. Total emails sent today: {emails_sent_today}")

if __name__ == "__main__":
    process_emails()