# extract_product_links.py

import json
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nav_structure.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/product_links.json")

def extract_product_links():
    with open(INPUT_FILE) as f:
        nav_data = json.load(f)

    product_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        page = context.new_page()

        for entry in nav_data:
            try:
                url = entry["url"]
                category = entry["category"]
                label = entry["label"]

                print(f"\n🔎 Visiting {label} under {category}")
                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)

                # Accept cookies if needed
                try:
                    page.wait_for_selector("button:has-text('Accept')", timeout=3000)
                    page.click("button:has-text('Accept')")
                    print("✅ Accepted cookies")
                    page.wait_for_timeout(1000)
                except:
                    print("⚠️ No cookie popup")

                # First try modern card layout
                cards = page.query_selector_all("a.card--product")

                # Fallback if none found
                if len(cards) == 0:
                    print("⚠️ No .card--product found, checking for .product-column blocks")
                    cards = page.query_selector_all(".product-column")

                print(f"   ➤ Found {len(cards)} potential product entries")

                for card in cards:
                    href = card.get_attribute("href")

                    # If fallback layout, look inside
                    if not href:
                        title_link = card.query_selector(".views-field-title a")
                        if title_link:
                            href = title_link.get_attribute("href")

                    if href:
                        full_url = urljoin(url, href)
                        product_links.append({
                            "category": category,
                            "brand": label,
                            "product_url": full_url
                        })

            except Exception as e:
                print(f"❌ Error with {entry['label']}: {e}")

        browser.close()

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(product_links, f, indent=2)
    print(f"\n✅ Saved {len(product_links)} product links to product_links.json")

if __name__ == "__main__":
    extract_product_links()
