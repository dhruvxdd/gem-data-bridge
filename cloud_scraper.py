import json
import re
import requests
from bs4 import BeautifulSoup

def run_cloud_crawl():
    print("Initializing Cloud Scraper Workflow...")
    landing_url = "https://bidplus.gem.gov.in/all-bids"
    api_url = "https://bidplus.gem.gov.in/all-bids-data"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    session = requests.Session()
    
    try:
        # Phase 1: Secure Handshake
        res = session.get(landing_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find("input", {"name": "csrf_bd_gem_nk"})
        
        if csrf_input:
            csrf_token = csrf_input.get("value")
        else:
            for hidden in soup.find_all("input", type="hidden"):
                if "csrf" in str(hidden.get("name")).lower() or len(str(hidden.get("value"))) == 32:
                    csrf_token = hidden.get("value")
                    break
        
        if not csrf_token:
            csrf_token = session.cookies.get("csrf_bd_gem_nk")
            
        if not csrf_token:
            print("Token extraction failed.")
            return

        print(f"Handshake complete. Token verified: {csrf_token[:8]}")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["Referer"] = landing_url
        
        # Pull page 1 data
        form_payload = {
            "payload": json.dumps({
                "page": 1,
                "param": {
                    "searchBid": "", "searchType": "fullText",
                    "filter": {
                        "bidStatusType": "ongoing_bids", "byType": "all", "highBidValue": "",
                        "byEndDate": {"from": "", "to": ""}, "sort": "Bid-End-Date-Oldest"
                    }
                }
            }),
            "csrf_bd_gem_nk": csrf_token
        }
        
        print("Fetching payload data block...")
        api_res = session.post(api_url, data=form_payload, headers=headers, timeout=15)
        
        if api_res.status_code == 200:
            data = api_res.json()
            docs = data.get("response", {}).get("response", {}).get("docs", [])
            print(f"Harvested {len(docs)} live data documents.")
            
            # Export raw data to a file inside the repository
            with open("gem_live_feeds.json", "w") as f:
                json.dump(docs, f, indent=4)
                print("Exported data matrix to gem_live_feeds.json successfully.")
        else:
            print(f"API Error Code: {api_res.status_code}")
            
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    run_cloud_crawl()
