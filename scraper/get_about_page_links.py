import os
import json
import logging
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.madewithnestle.ca/about-us"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/about_links.json")

def scrape_about_links():
    about_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        page = browser.new_page()
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        link_elements = page.query_selector_all("main a")

        for el in link_elements:
            try:
                href = el.get_attribute("href")
                text = el.inner_text().strip()

                if href and href.startswith("/about-us"):
                    about_links.append({
                        "title": text,
                        "url": "https://www.madewithnestle.ca" + href
                    })

            except Exception as e:
                logger.warning(f"Error processing a link: {e}")

        browser.close()

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(about_links, f, indent=2)

    logger.info(f"Saved {len(about_links)} 'About Us' links to {OUTPUT_FILE}")

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"'About Us' links already exist at {OUTPUT_FILE}. Skipping.")
    else:
        scrape_about_links()

if __name__ == "__main__":
    run()
