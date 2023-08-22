import configparser
import os
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sleep_interval_timer = 900 # sleep interval timer in seconds

# Read the website configurations
config = configparser.ConfigParser(interpolation=None)
config.read('config.cfg')

# Read the Telegram configurations
telegram_config = configparser.ConfigParser()
telegram_config.read('telegram.cfg')
telegram_token = telegram_config['telegram']['token']
telegram_chat_id = telegram_config['telegram']['chat_id']


def notify_telegram(message: str, token: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    response = requests.get(url)
    return response.status_code == 200


def fetch_latest_apartment(url: str, html_tag: str, html_class: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    tag = soup.find(html_tag, class_=html_class)
    return tag.text.strip() if tag else None


def fetch_latest_apartment_with_selenium(url: str, html_tag: str, html_class: str):
    options = Options()
    options.add_argument('--headless')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(5)

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find the tag using the given HTML tag and class
        tag = soup.find(html_tag, class_=html_class)

        # Don't forget to close the WebDriver
        driver.quit()
        print(tag.text.strip())

        # Return the desired value (modify as needed)
        return tag.text.strip() if tag else None
    except Exception as e:
        print(f'Error occured while using selenium:{e}')
        driver.quit()
        return None


def main():
    # Loop through config file site sections
    for site in config.sections():
        url = config[site]['url']
        html_tag = config[site]['html_tag']
        html_class = config[site]['html_class']
        filename = config[site]['filename']
        use_selenium = config[site].get('use_selenium', 'no').lower() == 'yes'

        if use_selenium:
            print(f'Fetching {site} using selenium... Beetje geduld...')
            latest_apartment = fetch_latest_apartment_with_selenium(url, html_tag, html_class)
        else:
            print(f'Fetching {site}...')
            latest_apartment = fetch_latest_apartment(url, html_tag, html_class)

        if latest_apartment is None:
            print(f"Failed to fetch latest apartment for site: {site}")
            continue

        # Check memory files for last scanned appartments
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                stored_apartment = file.read().strip()

            # New appartment if last name is not new name, could also be that an appartment is sold. Lets see how
            # this plays out
            if stored_apartment != latest_apartment:
                print('New appartment!')
                message = f"New apartment found on {url}: {latest_apartment}"
                telegram_status = notify_telegram(message, telegram_token, telegram_chat_id)
                if not telegram_status:
                    print('Error sending telegram message')

            elif stored_apartment == latest_apartment:
                print(f'No New Appartments on {site}')

        with open(filename, 'w') as file:
            file.write(latest_apartment)


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f'An error has occured {e}')
        sleep(sleep_interval_timer)
