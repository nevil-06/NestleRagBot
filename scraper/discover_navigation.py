# Stage 1: discover_navigation.py
# Updated: Multi-level hover navigation to extract categories and product links from the navbar

from playwright.sync_api import sync_playwright
import json
import os
from urllib.parse import urljoin

BASE_URL = "https://www.madewithnestle.ca/"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nav_structure.json")
nav_data = []

def discover_full_hover_menu():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Accept cookies
        try:
            page.click("button:has-text('Accept')", timeout=5000)
            print("✅ Accepted cookies")
        except:
            print("⚠️ No cookie banner found")

        # Hover over Brand
        try:
            page.hover("nav >> text=Brand")
            page.wait_for_timeout(1500)
            print("✅ Hovered on Brand")
        except Exception as e:
            print(f"❌ Failed to hover on Brand: {e}")
            browser.close()
            return

        # Get subcategories under Brand (e.g., Chocolates & Treats)
        submenus = page.query_selector_all(".menu-level-2-ul > li")
        print(f"🔎 Found {len(submenus)} subcategories")

        for submenu in submenus:
            try:
                title = submenu.inner_text().strip().split("\n")[0]  # Clean category name
                submenu.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                submenu.hover()
                page.wait_for_timeout(1000)

                product_links = submenu.query_selector_all(".menu-level-3-ul a")
                for link in product_links:
                    label = link.inner_text().strip()
                    href = link.get_attribute("href")
                    if href and label:
                        nav_data.append({
                            "category": title,
                            "label": label,
                            "url": urljoin(BASE_URL, href)
                        })
            except Exception as e:
                print(f"❌ Failed submenu: {e}")

        browser.close()

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(nav_data, f, indent=2)
    print(f"✅ Saved {len(nav_data)} category/subcategory links")

if __name__ == "__main__":
    discover_full_hover_menu()
