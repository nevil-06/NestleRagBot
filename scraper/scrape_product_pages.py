import json
import os
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/product_links.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_product_data.json")
FAILED_FILE = os.path.join(os.path.dirname(__file__), "../data/failed_products.json")

ua = UserAgent()

def scrape():
    with open(INPUT_FILE) as f:
        product_links = json.load(f)

    scraped = []
    failed = []

    for entry in product_links:
        url = entry["product_url"]
        category = entry["category"]
        brand = entry["brand"]

        logger.info(f"Fetching: {url}")

        headers = {
            "User-Agent": ua.random,
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "lxml")

            container = soup.select_one("div.product-detail-wrapper-global > div")
            if not container:
                logger.warning("Skipping — no container found.")
                failed.append(url)
                continue

            raw_texts = [text.strip() for text in container.stripped_strings if text.strip()]

            ingredients = []
            ingredients_tags = soup.select("div.field--name-field-ingredient-fullname, div.sub-ingredients p")
            ingredients.extend(tag.get_text(strip=True) for tag in ingredients_tags if tag.get_text(strip=True))

            if not ingredients:
                for div in soup.select("div.sub-ingredients"):
                    text = div.get_text(strip=True)
                    if text:
                        ingredients.append(text)

            if not ingredients:
                logger.warning(f"No ingredients found for {url}")

            scraped.append({
                "url": url,
                "brand": brand,
                "category": category,
                "raw_data": raw_texts,
                "explicit_ingredients": ingredients,
            })

            time.sleep(1)

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e.__class__.__name__}: {e}")
            failed.append(url)

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(scraped, f, indent=2)

    with open(FAILED_FILE, "w") as f:
        json.dump(failed, f, indent=2)

    logger.info(f"Attempted: {len(product_links)} products")
    logger.info(f"Successfully scraped: {len(scraped)}")
    logger.info(f"Failed: {len(failed)} (saved to {FAILED_FILE})")

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Full product data already exists at {OUTPUT_FILE}. Skipping.")
    else:
        scrape()

if __name__ == "__main__":
    run()
