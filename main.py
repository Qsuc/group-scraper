
import requests
import random
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Load configuration
def load_config():
    try:
        with open('config.txt', 'r') as f:
            config = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key.strip()] = value.strip()
            
            # Validate and convert values
            return {
                'use_proxies': config.get('proxies', 'false').lower() == 'true',
                'webhook_url': config.get('webhook', '').strip('"\' '),
                'threads': int(config.get('threads', 5)),
                'member_hit_threshold': int(config.get('member_hit_threshold', 0))
            }
    except (FileNotFoundError, ValueError):
        # Create default config if missing or invalid
        default_config = """# Configuration file
proxies = false
webhook = ""
threads = 5
member_hit_threshold = 0
"""
        with open('config.txt', 'w') as f:
            f.write(default_config)
        return {
            'use_proxies': False,
            'webhook_url': '',
            'threads': 5,
            'member_hit_threshold': 0
        }

CONFIG = load_config()

# Load proxies if enabled
PROXIES = []
if CONFIG['use_proxies']:
    try:
        with open('proxies.txt', 'r') as f:
            PROXIES = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Proxy file not found. Continuing without proxies.")
        CONFIG['use_proxies'] = False

# Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None

def get_group_data(group_id, proxy=None, retry_count=0):
    url = f'https://groups.roblox.com/v1/groups/{group_id}'
    max_retries = 3
    
    try:
        if proxy:
            response = requests.get(
                url,
                headers=HEADERS,
                proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                timeout=15
            )
        else:
            response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # Group doesn't exist
        elif response.status_code == 429:  # Rate limited
            if retry_count < max_retries:
                wait_time = (2 ** retry_count) + random.uniform(1, 3)  # Exponential backoff
                print(f"[RATE LIMIT] Group {group_id} - waiting {wait_time:.1f}s before retry {retry_count + 1}/{max_retries}")
                time.sleep(wait_time)
                return get_group_data(group_id, proxy, retry_count + 1)
            else:
                print(f"[RATE LIMIT] Group {group_id} - max retries exceeded")
                return None
        else:
            print(f"[DEBUG] Group {group_id} returned status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Network error for group {group_id}: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON decode error for group {group_id}: {str(e)}")
        return None

# Group IDs below this number are from before 2015
MAX_OLD_GROUP_ID = 1000000  # Adjust this number based on known group ID ranges

def has_no_owner(group_data):
    return group_data.get('owner') is None

def send_to_discord(group_data, hit_type="unclaimed"):
    if not CONFIG['webhook_url']:
        return False
    
    group_name = group_data.get('name', 'Unknown Group')
    group_id = group_data.get('id')
    members = group_data.get('memberCount', 0)
    group_link = f"https://www.roblox.com/groups/{group_id}"
    
    if hit_type == "unclaimed":
        title = "🎯 Unclaimed Roblox Group Found!"
        color = 0x00ff00
    else:  # member_hit
        title = f"👥 High Member Group Found! ({members} members)"
        color = 0xffa500
    
    embed = {
        "title": title,
        "fields": [
            {"name": "HIT:", "value": group_name, "inline": False},
            {"name": "LINK:", "value": f"[Click here]({group_link})", "inline": False},
            {"name": "MEMBERS:", "value": str(members), "inline": True},
            {"name": "ID:", "value": str(group_id), "inline": True}
        ],
        "color": color,
        "footer": {"text": "made by qsuc"},
        "url": group_link
    }
    
    try:
        requests.post(
            CONFIG['webhook_url'],
            json={"embeds": [embed]},
            headers={'Content-Type': 'application/json'}
        )
        return True
    except:
        return False

def worker():
    while True:
        # Only check group IDs that are known to be from before 2015
        group_id = random.randint(1, MAX_OLD_GROUP_ID)
        proxy = get_random_proxy() if CONFIG['use_proxies'] else None
        
        print(f"[CHECKING] Group {group_id}")
        data = get_group_data(group_id, proxy)
        
        if data:
            created = data.get('created', 'Unknown')
            members = data.get('memberCount', 0)
            owner = data.get('owner')
            group_name = data.get('name', 'Unknown Group')
            
            if has_no_owner(data):
                print(f"[HIT - UNCLAIMED] {group_name} | Members: {members} | ID: {group_id}")
                if CONFIG['webhook_url']:
                    send_to_discord(data, "unclaimed")
            elif CONFIG['member_hit_threshold'] > 0 and members >= CONFIG['member_hit_threshold']:
                print(f"[HIT - HIGH MEMBERS] {group_name} | Members: {members} | ID: {group_id}")
                if CONFIG['webhook_url']:
                    send_to_discord(data, "member_hit")
            else:
                print(f"[SKIP] Group {group_id} - has owner, {members} members")
        else:
            print(f"[ERROR] Could not fetch data for group {group_id}")
        
        time.sleep(random.uniform(0.5, 1.5))

def main():
    print(f"Starting scraper with {CONFIG['threads']} threads | Proxies: {'ON' if CONFIG['use_proxies'] else 'OFF'}")
    
    with ThreadPoolExecutor(max_workers=CONFIG['threads']) as executor:
        for _ in range(CONFIG['threads']):
            executor.submit(worker)

if __name__ == "__main__":
    main()
