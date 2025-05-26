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

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/about_links.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_articles.json")

def scrape_full_articles():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file with article links not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        about_links = json.load(f)

    full_articles = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        page = browser.new_page()

        for i, item in enumerate(about_links):
            try:
                page.goto(item["url"])
                page.wait_for_load_state("networkidle")

                title = page.query_selector("h1").inner_text().strip()

                paragraphs = []
                for para in page.query_selector_all("main p"):
                    text = para.inner_text().strip()
                    if text:
                        paragraphs.append(text)

                full_articles.append({
                    "title": title,
                    "url": item["url"],
                    "content": paragraphs
                })

                logger.info(f"[{i + 1}/{len(about_links)}] Scraped: {title}")

            except Exception as e:
                logger.warning(f"Failed to scrape {item['url']}: {e}")

        browser.close()

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_articles, f, indent=2)

    logger.info(f"Saved {len(full_articles)} articles to {OUTPUT_FILE}")

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Full article data already exists at {OUTPUT_FILE}. Skipping.")
    else:
        scrape_full_articles()

if __name__ == "__main__":
    run()
