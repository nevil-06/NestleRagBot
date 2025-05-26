import json
import os
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_product_data.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/structured_product_data.json")

def clean_text(text):
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()

def parse_product_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    parsed_data = []

    for item in raw_data:
        parsed_item = {
            "name": item.get("name", "").strip(),
            "category": item.get("category", "").strip(),
            "brand": item.get("brand", "").strip(),
            "weight": item.get("weight", "").strip(),
            "url": item.get("url", "").strip(),
            "ingredients": "",
            "nutrition": "",
            "features": "",
            "description": ""
        }

        sections = item.get("description", "").lower().split("\n")
        for section in sections:
            section_clean = clean_text(section)

            if "ingredients" in section:
                parsed_item["ingredients"] += section_clean + " "
            elif "nutrition" in section:
                parsed_item["nutrition"] += section_clean + " "
            elif "features" in section or "benefits" in section:
                parsed_item["features"] += section_clean + " "
            else:
                parsed_item["description"] += section_clean + " "

        for key in ["ingredients", "nutrition", "features", "description"]:
            parsed_item[key] = clean_text(parsed_item[key])

        parsed_data.append(parsed_item)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2)

    logger.info(f"Structured {len(parsed_data)} product entries to {OUTPUT_FILE}")

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Structured product data already exists at {OUTPUT_FILE}. Skipping.")
    else:
        parse_product_data()

if __name__ == "__main__":
    run()
