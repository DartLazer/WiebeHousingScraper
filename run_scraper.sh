#!/bin/bash

source /home/rik/WiebeHousingScraper/venv/bin/activate
PYTHONUNBUFFERED=1 python /home/rik/WiebeHousingScraper/housing_scraper.py >> /home/rik/WiebeHousingScraper/housing_scraper.log 2>&1 &
