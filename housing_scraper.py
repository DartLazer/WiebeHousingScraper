import configparser
import os
from time import sleep, time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

sleep_interval_timer = 900  # sleep interval timer in seconds

# Read the website configurations
config = configparser.ConfigParser(interpolation=None)
config.read('config.cfg')


def read_stored_tag(filename: str) -> str | None:
    """
    Reads a stored tag value from a predefined local text file. This so states are preserved in between sessions
    :param filename: filename/filepath of the file.
    :return: contents of the file as string
    """
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return file.read().strip()
    return None


def write_stored_tag(filename: str, tag: str) -> None:
    """
    Writes a new tag value from a website to a local text file.
    :param filename: new filename/filepath
    :param tag: Contents of the tag
    :return: None
    """
    with open(filename, 'w') as file:
        file.write(tag)


def handle_new_tag_found(url: str, latest_tag: str) -> None:
    """
    Actions to perform when a new tag is found.
    :param url: URL at which the new tag is found
    :param latest_tag: Conents of the new tag
    :return:
    """
    print('New apartment!')
    message = f"New apartment found on {url}: {latest_tag}"
    telegram_status = notify_telegram(message)
    if not telegram_status:
        print('Error sending telegram message')


def notify_telegram(message: str) -> bool:
    """
    Send a notification to the user via Telegram with a predfined message
    :param message: String containing the message
    :return: If a 200 code was received from telegram
    """
    telegram_config = configparser.ConfigParser()
    telegram_config.read('telegram.cfg')
    telegram_token = telegram_config['telegram']['token']
    telegram_chat_id = telegram_config['telegram']['chat_id']
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chat_id}&text={message}"
    response = requests.get(url)
    return response.status_code == 200


def find_newest_tag_in_page(soup_page: BeautifulSoup, target_html_tag: str, target_html_class: str):
    """
    Scans a beautiful soup object for a taget html tag and target html class
    :param soup_page: The page that was just visited and converted to a bs4 object
    :param target_html_tag: html tag to look for
    :param target_html_class: html class to look for
    :return: The stripped string of the found html tag, or else None
    """
    tag = soup_page.find(target_html_tag, class_=target_html_class)

    # Return the desired value (modify as needed)
    return tag.text.strip() if tag else None


def fetch_website(url: str) -> BeautifulSoup | None:
    """
    Use python requests module to obtain a specific website. Convert it to a BS4 object
    :param url: Target url
    :return:
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if the HTTP status code is 4xx or 5xx
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException as e:
        print(f"An error occurred while fetching the URL {url}: {e}")
        return None


def fetch_website_using_selenium(url: str) -> BeautifulSoup | None:
    """
    Use Selenium to visit a website and convert its contents to a bs4 object
    :param url: target URL
    :return: Bs4 object or None depending on the success of reaching the website.
    """

    options = Options()
    options.add_argument('--headless')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        # Explicitly wait for the element to become present on the page
        WebDriverWait(driver, 20).until(
            ec.presence_of_all_elements_located
        )

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        driver.quit()

        return soup
    except Exception as error_message:
        print(f'Error occurred while using selenium:{error_message}')
        driver.quit()
        return None


def main():
    print('Checking all websites for new entries...')
    # Loop through config file site sections
    for site in config.sections():
        url = config[site]['url']
        html_tag = config[site]['html_tag']
        html_class = config[site]['html_class']
        filename = config[site]['filename']
        use_selenium = config[site].get('use_selenium', 'no').lower() == 'yes'

        if use_selenium:
            soup_page = fetch_website_using_selenium(url)
        else:
            soup_page = fetch_website(url)

        latest_tag = find_newest_tag_in_page(soup_page, html_tag, html_class)

        if latest_tag is None:
            message = f"ERROR!!! Unable to find tag {html_tag} and class {html_class} on website: {site}"
            print(message)
            # notify_telegram(message)
            continue

        previous_stored_tag = read_stored_tag(filename)

        if previous_stored_tag and previous_stored_tag != latest_tag:
            print(f'New listing found on {site} at {url}!')
            handle_new_tag_found(url, latest_tag)

        write_stored_tag(filename, latest_tag)


if __name__ == "__main__":
    while True:
        start_time = time()
        try:
            main()
        except Exception as e:
            print(f'An error has occurred {e}')
        end_time = time()
        elapsed_time = end_time - start_time
        sleep_time = max(sleep_interval_timer - elapsed_time, 0)  # Ensuring the sleep time is never negative
        print(f'Script finished, sleeping for {sleep_time} seconds')
        sleep(sleep_time)
