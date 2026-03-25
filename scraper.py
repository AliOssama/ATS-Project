import requests
from datetime import datetime

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