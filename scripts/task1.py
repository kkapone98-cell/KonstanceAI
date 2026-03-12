import re

import requests


def parse_marketplace_listings(url):

    response = requests.get(url)

    if response.status_code != 200:

        raise Exception(f"Failed to fetch marketplace listings, status code: {response.status_code}")


    listings = response.text

    listings = listings.split('<li>')  # Assuming listings are in <li> tags


    parsed_listings = []

    for listing in listings:

        if '<title>' in listing and '</title>' in listing:

            title_match = re.search(r'<title>(.*?)</title>', listing)

            if title_match:

                title = title_match.group(1)

            else:

                continue  # Skip this listing if no title is found


        if '<span