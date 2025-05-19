import os
import json
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nav_structure.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/product_links.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def extract_product_links():
    with open(INPUT_FILE) as f:
        nav_data = json.load(f)

    all_links = []

    for entry in nav_data:
        base_url = entry["url"]
        category = entry["category"]
        brand = entry["label"]
        print(f"\n🔎 Scraping brand: {brand} under {category}")

        page_num = 0
        while True:
            paged_url = f"{base_url}?page={page_num}" if page_num > 0 else base_url
            print(f"   🔄 Page {page_num + 1}: {paged_url}")
            res = requests.get(paged_url, headers=HEADERS)
            if res.status_code != 200:
                print("   ❌ Failed to load page")
                break

            soup = BeautifulSoup(res.text, "lxml")
            cards = soup.select("a.card--product")
            if not cards:
                cards = soup.select(".product-column")

            if not cards:
                print("   ✅ No more products found — stopping pagination")
                break

            for card in cards:
                href = card.get("href")
                if not href:
                    link_el = card.select_one(".views-field-title a")
                    if link_el:
                        href = link_el.get("href")

                if href:
                    full_url = urljoin(base_url, href)
                    all_links.append({
                        "category": category,
                        "brand": brand,
                        "product_url": full_url
                    })

            page_num += 1
            time.sleep(1)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_links, f, indent=2)

    print(f"\n✅ Saved {len(all_links)} product links to product_links.json")

if __name__ == "__main__":
    extract_product_links()
