import requests
from datetime import datetime

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Companies using Greenhouse or Lever
GREENHOUSE_COMPANIES = ["airbnb", "stripe", "hubspot"]
LEVER_COMPANIES = ["netflix", "palantir", "roblox"]

def check_jobs():
    found_jobs = []
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Check Greenhouse
    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        data = requests.get(url).json()
        for job in data.get('jobs', []):
            # You can add logic here to filter by 'updated_at' or keywords
            found_jobs.append(f"{company.upper()}: {job['title']} - {job['absolute_url']}")

    # 2. Check Lever
    for company in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        data = requests.get(url).json()
        for job in data:
            found_jobs.append(f"{company.upper()}: {job['text']} - {job['hostedUrl']}")
    
    return found_jobs

if __name__ == "__main__":
    results = check_jobs()
    for job in results:
        print(job)


def send_email(job_list):
    if not job_list:
        return

    message = Mail(
        from_email='aly.ossama.aly@gmail.com',
        to_emails='aly.ossama.aly@gmail.com',
        subject='Daily Job Feed: New Opportunities',
        html_content=f"<p>Here are the jobs found in the last 24h:</p><ul>{''.join([f'<li>{j}</li>' for j in job_list])}</ul>"
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")