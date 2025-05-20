# scrape_product_pages.py

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/product_links.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_product_data.json")
FAILED_FILE = os.path.join(os.path.dirname(__file__), "../data/failed_products.json")

ua = UserAgent()

def scrape():
    with open(INPUT_FILE) as f:
        product_links = json.load(f)

    scraped = []
    failed = []

    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9",
    }

    for entry in product_links:
        url = entry["product_url"]
        category = entry["category"]
        brand = entry["brand"]

        print(f"\n🔎 Fetching: {url}")

        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "lxml")

            container = soup.select_one("div.product-detail-wrapper-global > div")
            if not container:
                print("⚠️ Skipping — no container found.")
                failed.append(url)
                continue

            print("   ➤ Container found, extracting text...")

            raw_texts = [text.strip() for text in container.stripped_strings if text.strip()]

            scraped.append({
                "url": url,
                "brand": brand,
                "category": category,
                "raw_data": raw_texts
            })

            time.sleep(1)

        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e.__class__.__name__}: {e}")
            failed.append(url)

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(scraped, f, indent=2)

    with open(FAILED_FILE, "w") as f:
        json.dump(failed, f, indent=2)

    print(f"\n✅ Attempted: {len(product_links)} products")
    print(f"✅ Successfully scraped: {len(scraped)}")
    print(f"❌ Failed: {len(failed)} (saved to failed_products.json)")

if __name__ == "__main__":
    scrape()
