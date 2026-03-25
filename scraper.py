import requests
import google.generativeai as genai
import time
import json
import os
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- CONFIGURATION ---
TARGET_TITLES = ["Software Engineer", "Developer", "AI Engineer", "Forward Deployed Engineer"]
EXCLUDE_KEYWORDS = ["Staff", "Principal", "Lead", "Manager", "Founding"]

GREENHOUSE_COMPANIES = ["airbnb", "stripe", "hubspot"]
LEVER_COMPANIES = ["palantir", "netflix", "roblox"]

def get_formatted_date(date_val):
    try:
        if isinstance(date_val, int):
            return datetime.fromtimestamp(date_val / 1000.0).strftime('%Y-%m-%d')
        return date_val.split('T')[0]
    except:
        return "Unknown Date"

def is_recent(date_val, days_ago=1):
    if not date_val: return False
    cutoff = datetime.now() - timedelta(days=days_ago)
    try:
        job_date = datetime.fromtimestamp(date_val / 1000.0) if isinstance(date_val, int) else datetime.strptime(date_val.split('T')[0], '%Y-%m-%d')
        return job_date >= cutoff
    except:
        return False

def is_title_match(job_title):
    title_lower = job_title.lower()
    return any(t.lower() in title_lower for t in TARGET_TITLES) and not any(e.lower() in title_lower for e in EXCLUDE_KEYWORDS)

def check_jobs(days_ago=1):
    found_jobs = []
    
    # Greenhouse Logic
    for company in GREENHOUSE_COMPANIES:
        try:
            # Cleanly joined URL
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            res = requests.get(url.strip()) 
            if res.status_code == 200:
                for job in res.json().get('jobs', []):
                    if is_recent(job.get('updated_at'), days_ago) and is_title_match(job.get('title', '')):
                        found_jobs.append(f"[{get_formatted_date(job.get('updated_at'))}] GREENHOUSE - {company.upper()}: {job['title']} - {job['absolute_url']}")
        except Exception as e: 
            print(f"Greenhouse Error {company}: {e}")

    # Lever Logic
    for company in LEVER_COMPANIES:
        try:
            # Cleanly joined URL
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            res = requests.get(url.strip())
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for job in data:
                        title = job.get('text', '')
                        if is_recent(job.get('createdAt'), days_ago) and is_title_match(title):
                            found_jobs.append(f"[{get_formatted_date(job.get('createdAt'))}] LEVER - {company.upper()}: {title} - {job.get('hostedUrl')}")
        except Exception as e: 
            print(f"Lever Error {company}: {e}")
            
    return found_jobs

def agent_filter(job_list):
    if not job_list:
        return "No jobs found today."

    api_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    print("⏳ Cooling down for 10s...")
    time.sleep(10)

    payload = {
        "contents": [{
            "parts": [{"text": f"Summarize these jobs for a developer. Pick top 3. Return as HTML <ul><li>: {job_list}"}]
        }]
    }

    headers = {'Content-Type': 'application/json'}

    try:
        print("🧠 Hitting API directly...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 429:
            print("❌ Quota still locked. Your 'Default Project' has 0 limit.")
            return "<ul>" + "".join([f"<li>{j}</li>" for j in job_list]) + "</ul>"
            
        response.raise_for_status()
        data = response.json()
        ai_text = data['candidates'][0]['content']['parts'][0]['text']
        return ai_text.replace("```html", "").replace("```", "").strip()

    except Exception as e:
        print(f"Direct API Error: {e}")
        return "<ul>" + "".join([f"<li>{j}</li>" for j in job_list]) + "</ul>"

def send_email(html_body):
    if not html_body: return
    message = Mail(
        from_email='aly.ossama.aly@gmail.com',
        to_emails='aly.ossama.aly@gmail.com',
        subject='Daily Job Feed: AI Agent Summary',
        html_content=html_body
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
        print("Email sent successfully!")
    except Exception as e: print(f"Email Error: {e}")

if __name__ == "__main__":
    print("🤖 Agent waking up...")
    raw_results = check_jobs(days_ago=3)
    if raw_results:
        summary = agent_filter(raw_results)
        send_email(summary)
    else:
        print("No matches found.")