import configparser
import datetime
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


def ensure_temp_folder_exists():
    """
    Ensures that the 'temp_files' folder exists, and if not, creates it.
    """
    folder_path = 'temp_files'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def remove_duplicates(lst: list) -> list:
    """
    Removes duplicates from a list while preserving the order of the elements.
    :param lst: Input list
    :return: List with duplicates removed
    """
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def read_stored_tags(filename: str) -> list:
    """
    Reads a file containing found tags and returns them as a list
    :param filename: filename/filepath of the file.
    :return: contents of the file as string
    """
    filename = os.path.join('temp_files', filename)
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []


def write_stored_tags(filename: str, tags: list) -> None:
    """
        Writes a new tag value from a website to a local text file.
        :param filename: new filename/filepath
        :param tags: A list containing tags
        :return: None
        """
    filename = os.path.join('temp_files', filename)
    with open(filename, 'w') as file:
        file.write('\n'.join(tags))


def handle_new_tag_found(url: str, amount_of_new_tags_found: int) -> None:
    """
    Actions to perform when a new tag is found.
    :param url: URL at which the new tag is found
    :param amount_of_new_tags_found:Amount of new tags found
    :return:
    """
    message = f"{amount_of_new_tags_found} new apartment(s) found on {url}"
    print(message)
    telegram_status = notify_telegram(message)
    if not telegram_status:
        print('Error sending telegram message')


def notify_telegram(message: str) -> bool:
    """
    Send a notification to the user via Telegram with a predefined message
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


def find_all_tags_in_page(soup_page: BeautifulSoup, target_html_tag: str, target_html_class: str) -> list:
    """
    Scans a beautiful soup object for a target html tag and target html class
    :param soup_page: The page that was just visited and converted to a bs4 object
    :param target_html_tag: html tag to look for
    :param target_html_class: html class to look for
    :return: A list of stripped strings of the found html tags, or else an empty list
    """
    tags = soup_page.find_all(target_html_tag, class_=target_html_class)

    # Return the desired values (modify as needed)
    return [tag.text.strip() for tag in tags if tag]


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
    except requests.RequestException as error_message:
        print(f"An error occurred while fetching the URL {url}: {error_message}")
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
    ensure_temp_folder_exists()
    print('Checking all websites for new entries...')

    # Loop through config file site sections
    for site in config.sections():
        total_new_apartments = 0  # Keep track of the total number of new apartments
        section = config[site]
        url = section.get('url')
        html_tag = section.get('html_tag')
        html_class = section.get('html_class')
        filename = section.get('filename')
        use_selenium = section.get('use_selenium', 'no').lower() == 'yes'

        if use_selenium:
            soup_page = fetch_website_using_selenium(url)
        else:
            soup_page = fetch_website(url)

        found_tags = find_all_tags_in_page(soup_page, html_tag, html_class)
        previous_stored_tags = read_stored_tags(filename)

        new_apartments = [tag for tag in found_tags if tag not in previous_stored_tags]
        num_new_apartments = len(new_apartments)  # Number of new apartments for this site

        if new_apartments:
            total_new_apartments += num_new_apartments  # Increment the total count

        write_stored_tags(filename, found_tags)

        # Send a notification if any new apartments are found
        if total_new_apartments > 0 and previous_stored_tags:
            handle_new_tag_found(url, total_new_apartments)


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
        print(f'Script finished, sleeping for {sleep_time} seconds. Finished at{datetime.datetime.now()}')
        sleep(sleep_time)
