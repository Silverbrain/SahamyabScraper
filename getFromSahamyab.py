"""
Sahamyab Social Media Scraper
-----------------------------
This script fetches user messages from the Sahamyab social media platform,
where users share insights about Iran's stock market. The data is intended
for sentiment analysis and AI-based stock price prediction.

Features:
- Authenticates and refreshes tokens for Sahamyab API
- Iteratively fetches messages tagged with a specific stock symbol
- Saves messages to a CSV file for further analysis

Usage:
    python getFromSahamyab.py

Requirements:
    - requests
    - pandas
    - jdatetime
    - Python 3.6+
    - config.json file with required parameters
"""

import logging
from urllib.parse import quote
import requests as req
import pandas as pd
import json
import csv
import jdatetime as jdt
import datetime as dt
import time
import os
from typing import Tuple, List, Dict, Any

# Configure logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class bcolors:
    """
    ANSI color codes for optional colored terminal output (legacy, not used with logging).
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def to_datetime(_date: str) -> dt.datetime:
    """
    Convert an ISO 8601 string (e.g., '2020-08-01T12:34:56Z') to a Python datetime object.

    Args:
        _date (str): The ISO 8601 date string.

    Returns:
        datetime.datetime: The corresponding datetime object.
    """
    # Split date and time
    _date = str.split(_date, 'T')
    date = _date[0].split('-')
    time_part = _date[1].split(':')
    y = int(date[0])
    m = int(date[1])
    d = int(date[2])
    hh = int(time_part[0])
    mm = int(time_part[1])
    ss = int(time_part[2].split('Z')[0])
    _datetime = dt.datetime(y, m, d, hour=hh, minute=mm, second=ss)
    return _datetime


def refresh_token(token: str) -> Tuple[str, str, str]:
    """
    Refresh the Sahamyab API token.

    Args:
        token (str): The refresh token.

    Returns:
        Tuple[str, str, str]: (token_type, access_token, refresh_token)

    Raises:
        RuntimeError: If unable to acquire a new token.
    """
    url = 'https://www.sahamyab.com/auth/realms/sahamyab/protocol/openid-connect/token'
    header = {
        'Content-type': 'application/x-www-form-urlencoded',
        'Referer': 'https://www.sahamyab.com/sso.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40'
    }
    form_data = {
        'grant_type': 'refresh_token',
        'refresh_token': token,
        'client_id': 'sahamyab'
    }
    res = req.post(url, headers=header, data=form_data)
    if res.status_code == 200:
        res_json = res.json()
        logging.info("New token acquired.")
        return res_json['token_type'], res_json['access_token'], res_json['refresh_token']
    else:
        raise RuntimeError('Unable to acquire token')


def update_config_refresh_token(config_path: str, new_ref_token: str) -> None:
    """
    Update the refresh token in the config file.

    Args:
        config_path (str): Path to the config.json file.
        new_ref_token (str): The new refresh token to save.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['ref_token'] = new_ref_token
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.info('Refresh token updated in config.json.')
    except Exception as e:
        logging.error(f'Failed to update refresh token in config: {e}')


def load_data(token_type: str, access_token: str, n_page: int, l_id: str, symbol: str) -> List[Dict[str, Any]]:
    """
    Fetch a page of messages from Sahamyab API.

    Args:
        token_type (str): The type of the token (e.g., 'Bearer').
        access_token (str): The access token for authentication.
        n_page (int): The current page number (used for pagination).
        l_id (str): The last message ID fetched (for pagination).
        symbol (str): The stock symbol to fetch messages for.

    Returns:
        List[Dict[str, Any]]: List of message items (dicts).

    Raises:
        RuntimeError: If the response is bad or data is corrupted.
    """
    addr = 'https://www.sahamyab.com/app/twiter/list?v=0.1'
    data = {'tag': symbol} if n_page < 1 else {'id': str(l_id), 'tag': symbol}

    # Log the request data for debugging
    logging.debug(f"Request data: {data}")

    params = {
        'accept': 'application/json, text/plain, */*',
        'authorization': f'{token_type} {access_token}',
        'content-type': 'application/json',
        'referer': f'https://www.sahamyab.com/hashtag/{quote(symbol)}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40',
    }
    res = req.post(addr, headers=params, json=data)
    if res.status_code == 200:
        logging.info(f'Status code: {res.status_code}')
        try:
            items = res.json()['items']
            return items
        except Exception:
            raise RuntimeError('Data corrupted')
    else:
        raise RuntimeError(f'Bad response: {res.status_code}')


def scrape_sahamyab(
    file_name: str,
    symbol: str,
    ref_token: str,
    error_thold: int = 5,
    start_date: dt.datetime = dt.datetime(2020, 8, 1),
    config_path: str = 'config.json'
) -> None:
    """
    Main scraping loop for Sahamyab messages.

    Args:
        file_name (str): Output CSV file name.
        symbol (str): Stock symbol to fetch messages for.
        ref_token (str): Refresh token for authentication.
        error_thold (int): Error threshold before attempting token refresh.
        start_date (datetime): Stop scraping when this date is reached.
        config_path (str): Path to the config file for updating the refresh token.
    """
    last_id = ''
    date = dt.datetime.now()
    page = 0
    token_type = ''
    access_token = ''
    error_count = 0
    o_mode = ''

    # Try to refresh token before starting
    try:
        token_type, access_token, ref_token = refresh_token(ref_token)
        update_config_refresh_token(config_path, ref_token)
    except Exception as e:
        logging.error(f'Error refreshing token: {e}')
        return

    t = time.time()

    # Check if file exists to determine append or write mode
    if os.path.isfile(file_name):
        o_mode = 'a'
        df = pd.read_csv(file_name)
        last_id = df['id'].iloc[-1]
        page += 1
    else:
        o_mode = 'w'

    # Open the file and ensure it is closed on interrupt
    _file = open(file_name, mode=o_mode, encoding='utf8', newline='')
    try:
        field_names = ['id', 'time', 'user', 'content']
        writer = csv.DictWriter(_file, fieldnames=field_names)

        # Write header if new file
        if o_mode == 'w':
            writer.writeheader()

        repeat = False

        # Main scraping loop: fetch until reaching the start_date
        while date > start_date:
            if not repeat:
                logging.info(f'Page: {page} in progress...')

            # Send request to the API and handle errors
            try:
                items = load_data(token_type, access_token, page, last_id, symbol)
            except Exception as e:
                logging.error(f'Error on page {page}: {e}')
                error_count += 1
                if error_count == error_thold:
                    try:
                        token_type, access_token, ref_token = refresh_token(ref_token)
                        update_config_refresh_token(config_path, ref_token)
                    except Exception as e:
                        logging.warning(f'Unable to acquire access token: {e}')
                        break
                elif error_count >= error_thold + 5:
                    break
                continue

            last_item = items[-1]
            if last_id == last_item['id']:
                repeat = True
                continue
            last_id = last_item['id']

            # Write each item to CSV
            for item in items:
                row = {
                    'id': item['id'],
                    'time': to_datetime(item['sendTime']),
                    'user': item['senderUsername'],
                    'content': item['content']
                }
                date = row['time']
                logging.debug(f"Writing row: {row['id']} at {date}")
                writer.writerow(row)

            logging.info(f'Page: {page}: success | last date: {to_datetime(last_item["sendTime"])}')
            logging.info('-' * 60)
            repeat = False
            page += 1
            error_count = 0
    except KeyboardInterrupt:
        # Graceful termination on user interrupt
        logging.warning('Scraping interrupted by user. Closing file and saving progress...')
    finally:
        _file.close()
        logging.info(f'File "{file_name}" closed and data saved.')
        return

    elapsed = time.time() - t
    if error_count >= error_thold:
        logging.error(f"Error threshold reached. Program terminated! Elapsed: {elapsed:.2f} seconds.")
    else:
        logging.info(f'Successfully DONE. Elapsed: {elapsed:.2f} seconds.')


def main():
    """
    Entry point for the Sahamyab scraper script.
    Loads parameters from config.json (created with defaults if missing).
    """
    # Load configuration from config.json
    config_path = 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        # Default config if file does not exist
        config = {
            "file_name": "data.csv",
            "symbol": "شبندر",
            "error_thold": 5,
            "ref_token": "",
            "start_date": "2020-08-01"
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.info(f"Default config.json created. Please review and rerun if needed.")
    
    # Parse start_date from config
    start_date = dt.datetime.strptime(config["start_date"], "%Y-%m-%d")

    # Start the scraping process with loaded parameters
    scrape_sahamyab(
        file_name=config["file_name"],
        symbol=config["symbol"],
        ref_token=config["ref_token"],
        error_thold=int(config["error_thold"]),
        start_date=start_date,
        config_path=config_path
    )


if __name__ == "__main__":
    main()
