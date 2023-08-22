# Apartment Scraper

This script is designed to scrape apartment listings from various websites and notify users via Telegram when new apartments are found. It can be configured to use both `requests` and `Selenium` for scraping.

## Requirements

- Python 3.x
- BeautifulSoup
- Selenium
- requests

## Configuration

The script relies on two configuration files:

1. `config.cfg`: Contains the website configurations for scraping.
2. `telegram.cfg`: Contains the Telegram bot token and chat ID for notifications.

### Example `config.cfg`

```ini
[site_name]
url = https://example.com
html_tag = div
html_class = class-name
filename = filename.txt
use_selenium = yes
```

### Example Telegram.cfg

```ini
[telegram]
token = YOUR_BOT_TOKEN_HERE
chat_id = USER_CHAT_ID_HERE
```

# Usage
Configure the `config.cfg` and `telegram.cfg` files as per your requirements.

Run the script:

```bash
python housing_scraper.py
```

## Automatically Running the script at predefined times

To set up the script to automatically start on a specified time on Windows perform the following tasks

- Open the Task Scheduler by pressing Win + R, typing taskschd.msc, and hitting Enter.

- In the Task Scheduler, click on "Create Basic Task" in the Actions pane on the right-hand side.

- Give your task a name and optional description, then click "Next."

- Select "Daily" as the trigger if you want the script to run every day, alternatively you can also select at startup or
  login. Click "Next."

- Set the time you want the script to run and select the "Recur every" option if you want it to run daily. Click "Next."

- Choose "Start a program" as the action, and click "Next."

- Browse for your Python Installation (not this script) executable by clicking the "Browse" button. Typically, the
  Python executable is located at C:\(Program Files)\PythonXX\python.exe, where "XX" represents the version number.
  Select your Python executable and click "Open."

- In the "Start in" field, provide the directory where this script is located. For example, if your script is in C:
  \house_scraper\, you would enter C:\house_scraper\ in the "Start in" field.

- In the "Add arguments" field, provide the name of this script "housing_scraper.py"

Click "Next" and then "Finish" to create the task.
The script should now start daily at the specified time
Alternatively you can also set the script to start at boot (windows startup) so it will always run when the computer is
started.