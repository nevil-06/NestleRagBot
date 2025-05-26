import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.madewithnestle.ca/recipes"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nestle_recipes.json")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def scrape():
    params = {"_wrapper_format": "html", "page": 0}
    all_recipes = []

    while True:
        logger.info(f"Fetching page {params['page']}...")
        response = requests.get(BASE_URL, params=params, headers=headers)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch page {params['page']}. Status: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        recipe_links = soup.select('a.recipe-search-block[href]')

        if not recipe_links:
            logger.info("No more recipes found.")
            break

        for tag in recipe_links:
            href = tag['href']
            url = href if href.startswith("http") else f"https://www.madewithnestle.ca{href}"

            title = tag.select_one('h4.coh-heading')
            desc = tag.select_one('.recipe-desc p')
            image = tag.select_one('.recipe-block-image img')
            prep_time = tag.select_one('.stat-prep-time')
            cook_time = tag.select_one('.stat-cook-time')

            recipe = {
                "title": title.get_text(strip=True) if title else None,
                "url": url,
                "description": desc.get_text(strip=True) if desc else None,
                "image": image['src'] if image and image.has_attr('src') else None,
                "prep_time_mins": int(prep_time.text.strip()) if prep_time and prep_time.text.strip().isdigit() else None,
                "cook_time_mins": int(cook_time.text.strip()) if cook_time and cook_time.text.strip().isdigit() else None
            }

            all_recipes.append(recipe)

        params["page"] += 1
        time.sleep(1)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ Saved {len(all_recipes)} recipes to '{OUTPUT_FILE}'")

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Recipe data already exists at {OUTPUT_FILE}. Skipping.")
    else:
        scrape()

if __name__ == "__main__":
    run()
