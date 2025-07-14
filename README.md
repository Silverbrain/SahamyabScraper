# Sahamyab Social Media Scraper

This project is a Python-based web scraper designed to collect user messages from the Sahamyab social media platform, where users share insights and ideas about Iran's stock market. The collected data is intended for sentiment analysis and AI-based stock price prediction.

## Features
- Authenticates and refreshes tokens for the Sahamyab API
- Iteratively fetches messages tagged with a specific stock symbol
- Saves messages to a CSV file for further analysis

## Requirements
- Python 3.6+
- [requests](https://pypi.org/project/requests/)
- [pandas](https://pypi.org/project/pandas/)
- [jdatetime](https://pypi.org/project/jdatetime/)

## Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/sahamyab-scraper.git
   cd sahamyab-scraper
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
All parameters are managed via `config.json`:
```json
{
    "file_name": "data.csv",
    "symbol": "{SYMBOL}",
    "error_thold": 5,
    "ref_token": "{REFTOKEN}",
    "start_date": "2020-08-01"
}
```
- `file_name`: Output CSV file name
- `symbol`: Stock symbol to fetch messages for (e.g., "شبندر")
- `error_thold`: Error threshold before attempting token refresh
- `ref_token`: Sahamyab API refresh token (obtain from your account/session)
- `start_date`: Stop scraping when this date is reached (format: YYYY-MM-DD)

> **Note:** The refresh token in `config.json` is automatically updated whenever a new token is acquired.

## Usage
Run the scraper with:
```bash
python getFromSahamyab.py
```

- The script will create or update the output CSV file as specified in `config.json`.
- If interrupted (Ctrl+C), the script will close the file and save all progress.

## Output
- The output CSV will contain columns: `id`, `time`, `user`, `content`.

## Security Note
- The script uses secure HTTPS requests by default. Do **not** set `verify=False` in production.
- Keep your refresh token private and do not share it publicly.

## License
[MIT License](LICENSE)
