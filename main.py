
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
                'member_hit_threshold': int(config.get('member_hit_threshold', 0)),
                'unlocked_id': config.get('unlocked_id', 'false').lower() == 'true'
            }
    except (FileNotFoundError, ValueError):
        # Create default config if missing or invalid
        default_config = """# Configuration file
proxies = false
webhook = ""
threads = 5
member_hit_threshold = 0
unlocked_id = false
"""
        with open('config.txt', 'w') as f:
            f.write(default_config)
        return {
            'use_proxies': False,
            'webhook_url': '',
            'threads': 5,
            'member_hit_threshold': 0,
            'unlocked_id': False
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

def get_group_data(group_id, proxy=None):
    url = f'https://groups.roblox.com/v1/groups/{group_id}'

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
        elif response.status_code == 429:  # Rate limited
            print(f"[RATE LIMIT] Group {group_id} - waiting 5s...")
            time.sleep(5)
            return None
        return None
    except:
        return None

# Group IDs below this number are from before 2015
MAX_OLD_GROUP_ID = 1000000

def has_no_owner(group_data):
    return group_data.get('owner') is None

def is_community_closed_with_zero_members(group_data):
    """Check if group is community closed and has 0 members"""
    return (group_data.get('memberCount', 0) == 0 and 
            group_data.get('description', '').lower().find('community closed') != -1)

def send_to_discord(group_data, hit_type="unclaimed"):
    if not CONFIG['webhook_url']:
        return False

    group_name = group_data.get('name', 'Unknown Group')
    group_id = group_data.get('id')
    members = group_data.get('memberCount', 0)
    group_link = f"https://www.roblox.com/groups/{group_id}"

    if hit_type == "unclaimed":
        title = "🎯 Unclaimed Roblox Group Found! 🎯"
        color = 0x00ff88  # Bright green
        description = f"🚀 **A wild unclaimed group appeared!** 🚀"
    else:  # member_hit
        title = f"👥🔥 High Member Group Found! ({members} members) 🔥👥"
        color = 0xff6b35  # Bright orange
        description = f"💎 **High value target for user acquisition!** 💎"

    embed = {
        "title": title,
        "description": description,
        "fields": [
            {"name": "🎯 **HIT:**", "value": f"```{group_name}```", "inline": False},
            {"name": "🔗 **LINK:**", "value": group_link, "inline": False},
            {"name": "👥 **MEMBERS:**", "value": f"```{members}```", "inline": True},
            {"name": "🆔 **ID:**", "value": f"```{group_id}```", "inline": True}
        ],
        "color": color,
        "footer": {
            "text": "made by qsuc",
            "icon_url": "https://i.imgur.com/your-cat-image.png"
        },
        "image": {
            "url": "https://cdn.discordapp.com/attachments/1324775803480834090/1379271885942034543/image0.gif?ex=683fa28b&is=683e510b&hm=66a8b551371ef6f4c2ce31cd5d95b1641a2013fa08a6ed8ba8e63bab132d0b75&"
        },
        "url": group_link,
        "timestamp": datetime.utcnow().isoformat()
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
        # Check either old group IDs or completely random IDs based on unlocked_id setting
        if CONFIG['unlocked_id']:
            group_id = random.randint(1, 99999999)  # Completely random IDs
        else:
            group_id = random.randint(1, MAX_OLD_GROUP_ID)  # Only old group IDs

        proxy = get_random_proxy() if CONFIG['use_proxies'] else None

        print(f"[CHECKING] Group {group_id}")
        data = get_group_data(group_id, proxy)

        if data:
            members = data.get('memberCount', 0)
            owner = data.get('owner')
            group_name = data.get('name', 'Unknown Group')

            # Skip only if group is community closed with 0 members
            if is_community_closed_with_zero_members(data):
                print(f"[SKIP] Group {group_id} - community closed with 0 members")
            elif has_no_owner(data):
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
            print(f"[SKIP] Group {group_id} - no data or rate limited")

        time.sleep(random.uniform(1, 3))

def main():
    print(f"Starting scraper with {CONFIG['threads']} threads | Proxies: {'ON' if CONFIG['use_proxies'] else 'OFF'}")

    with ThreadPoolExecutor(max_workers=CONFIG['threads']) as executor:
        for _ in range(CONFIG['threads']):
            executor.submit(worker)

if __name__ == "__main__":
    main()
