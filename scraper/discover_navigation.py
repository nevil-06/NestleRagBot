# discover_navigation.py

from playwright.sync_api import sync_playwright
import json
import os
from urllib.parse import urljoin

BASE_URL = "https://www.madewithnestle.ca/"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nav_structure.json")
nav_data = []

def discover_brand_only():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # ✅ Accept cookies
        try:
            page.click("button:has-text('Accept')", timeout=5000)
            print("✅ Accepted cookies")
        except:
            print("⚠️ No cookie banner found")

        # ✅ Close optional modal popup
        try:
            page.click(".popup-close, .modal-close, .close-button", timeout=3000)
            print("✅ Closed modal popup")
        except:
            print("✅ No modal popup appeared")

        # ✅ Hover on "Brand" menu
        try:
            page.hover("nav >> text=Brand")
            page.wait_for_timeout(1500)
            print("✅ Hovered on 'Brand'")
        except Exception as e:
            print(f"❌ Failed to hover on 'Brand': {e}")
            browser.close()
            return

        # ✅ Find and loop through submenus
        submenus = page.query_selector_all(".menu-level-2-ul > li")
        print(f"🔎 Found {len(submenus)} subcategories under Brand")

        for submenu in submenus:
            try:
                title = submenu.inner_text().strip().split("\n")[0]
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

                # ✅ Exit after scraping "Quick-Mix Drinks"
                if title.lower() == "quick-mix drinks":
                    print(f"✅ Finished scraping '{title}' — stopping early.")
                    break

            except Exception as e:
                print(f"⚠️ Error in submenu '{title}': {e}")

        # ✅ Save and exit
        os.makedirs("data", exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(nav_data, f, indent=2)
        print(f"✅ Saved {len(nav_data)} links to {OUTPUT_FILE}")

        browser.close()

if __name__ == "__main__":
    discover_brand_only()
