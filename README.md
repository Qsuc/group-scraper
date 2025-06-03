
# Roblox Group Scraper

A Python tool to find unclaimed Roblox groups by scanning group IDs and checking for groups without owners.

## Features

- 🔍 Scans Roblox groups to find unclaimed ones
- 🚀 Multi-threaded scanning for faster results
- 🔗 Discord webhook integration for notifications
- 🌐 Proxy support for rate limit avoidance
- ⚙️ Easy configuration via config file
- 🛡️ Smart rate limit handling with exponential backoff
- 👥 Optional high-member group detection for user acquisition

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/roblox-group-scraper.git
cd roblox-group-scraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the scraper by editing `config.txt`:
   - Set your Discord webhook URL (optional)
   - Adjust thread count (1-5 recommended)
   - Enable proxies if you have a proxy list
   - Set member hit threshold for user acquisition opportunities

## Configuration

Edit `config.txt` to customize the scraper:

```
# Roblox Group Scraper Configuration
proxies = false
webhook = "YOUR_DISCORD_WEBHOOK_URL_HERE"
threads = 1
member_hit_threshold = 10
```

### Discord Webhook Setup

1. Create a Discord webhook in your server
2. Copy the webhook URL
3. Paste it in the `webhook` field in `config.txt`

### Proxy Support

If you want to use proxies:
1. Set `proxies = true` in config.txt
2. Create a `proxies.txt` file with one proxy per line in format: `ip:port`

### High-Member Group Detection

To find groups with high member counts for potential user acquisition:
1. Set `member_hit_threshold = 10` (or your preferred number) in config.txt
2. Groups with this many members or more will be flagged as hits
3. Set to `0` to disable this feature

## Usage

Run the scraper:
```bash
python main.py
```

The scraper will:
- Check random Roblox group IDs from before 2015
- Display results in the console
- Send notifications to Discord (if webhook configured)

## Output

When groups are found, you'll see:
```
[HIT - UNCLAIMED] Group Name | Members: 123 | ID: 456789
[HIT - HIGH MEMBERS] Popular Group | Members: 1500 | ID: 123456
```

Discord notifications include:
- Group name and link
- Member count
- Group ID
- Direct link to the group
- Different colors for unclaimed vs high-member groups

## Legal Notice

This tool is for educational purposes only. Please respect Roblox's Terms of Service and rate limits. Use responsibly.

## License

This project is open source and available under the MIT License.
