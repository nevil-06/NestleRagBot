import json
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nav_structure.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/product_links.json")


def extract_links():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Navigation data not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        nav_data = json.load(f)

    product_links = []

    for item in nav_data:
        url = item.get("url")
        label = item.get("label")
        category = item.get("category")

        if url and label:
            product_links.append({
                "category": category,
                "label": label,
                "url": url
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(product_links, f, indent=2)

    logger.info(f"Saved {len(product_links)} product links to {OUTPUT_FILE}")


def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Product links already exist at {OUTPUT_FILE}. Skipping extraction.")
    else:
        extract_links()


if __name__ == "__main__":
    run()
