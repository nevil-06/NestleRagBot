# scraper/scrape_recipes_list.py

import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://www.madewithnestle.ca"
LIST_URL = f"{BASE_URL}/recipes"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_recipe_links():
    response = requests.get(LIST_URL, headers=HEADERS)
    if response.status_code != 200:
        print("Failed to load page:", response.status_code)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for a in soup.select("a.recipe-card-link"):
        title = a.get("title") or a.text.strip()
        href = a.get("href")
        if href:
            links.append({
                "title": title,
                "url": BASE_URL + href
            })

    os.makedirs("data", exist_ok=True)
    with open("data/recipes_list.json", "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2)

    print(f"Scraped {len(links)} recipes.")
    return links

if __name__ == "__main__":
    scrape_recipe_links()
