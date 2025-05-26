import json
import requests
from bs4 import BeautifulSoup
import time
from collections import OrderedDict
import re
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/nestle_recipes.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_nestle_recipes.json")

# ---------- Cleaning Helpers ----------
def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = re.sub(r"[®™‡*]", "", text)
    text = text.replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_ingredients(ingredients):
    cleaned = []
    for item in ingredients:
        item = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", item)  # 1tsp → 1 tsp
        item = item.replace("tsp", "teaspoon").replace("tbsp", "tablespoon")
        cleaned.append(clean_text(item))
    return cleaned

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def extract_full_recipe(url):
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            logger.warning(f"Failed to fetch: {url}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        desc = soup.select_one(".recipe-desc p")
        description = desc.get_text(strip=True) if desc else None

        prep = soup.select_one(".stat-prep-time")
        cook = soup.select_one(".stat-cook-time")
        prep_time = int(prep.text.strip()) if prep and prep.text.strip().isdigit() else None
        cook_time = int(cook.text.strip()) if cook and cook.text.strip().isdigit() else None

        serving_tag = soup.select_one("span.serving-value.value")
        servings = int(re.search(r"\d+", serving_tag.get_text()).group()) if serving_tag and re.search(r"\d+", serving_tag.get_text()) else None

        skill_tag = soup.select_one("span.skill-level-value.value")
        skill_level = skill_tag.get_text(strip=True) if skill_tag else None

        ingredients = [
            tag.get_text(strip=True)
            for tag in soup.select("div.field--name-field-ingredient-fullname.field__item")
            if tag.get_text(strip=True)
        ]
        ingredients = list(OrderedDict.fromkeys(ingredients)) if ingredients else []

        raw_steps = [
            p.get_text(strip=True)
            for p in soup.select("article p.coh-paragraph")
            if p.get_text(strip=True)
        ]
        seen = OrderedDict()
        for step in raw_steps:
            seen[step] = None
        instructions = list(seen.keys())

        # CLEANING
        title = clean_text(title)
        description = clean_text(description)
        skill_level = clean_text(skill_level)
        ingredients = clean_ingredients(ingredients)
        instructions = [clean_text(i) for i in instructions]

        return {
            "title": title,
            "description": description,
            "prep_time_mins": prep_time,
            "cook_time_mins": cook_time,
            "servings": servings,
            "skill_level": skill_level,
            "ingredients": ingredients,
            "instructions": instructions,
            "url": url
        }

    except Exception as e:
        logger.error(f"Error at {url}: {e}")
        return None

def run():
    if os.path.exists(OUTPUT_FILE):
        logger.warning(f"Full recipe data already exists at {OUTPUT_FILE}. Skipping.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    enhanced = []

    for recipe in recipes:
        logger.info(f"Scraping: {recipe['title']}")
        details = extract_full_recipe(recipe["url"])
        time.sleep(1)

        if details:
            description = details.get("description") or recipe.get("description")
            description = clean_text(description) if description else None

            full_recipe = {
                "title": details["title"],
                "description": description,
                "prep_time_mins": details["prep_time_mins"] or recipe.get("prep_time_mins"),
                "cook_time_mins": details["cook_time_mins"] or recipe.get("cook_time_mins"),
                "servings": details["servings"],
                "skill_level": details["skill_level"],
                "ingredients": details["ingredients"],
                "instructions": details["instructions"],
                "url": recipe["url"]
            }

            if (
                full_recipe.get("instructions")
                and full_recipe["instructions"][0]
                and full_recipe.get("description")
                and isinstance(full_recipe["description"], str)
                and full_recipe["instructions"][0].strip().lower() == full_recipe["description"].strip().lower()
            ):
                full_recipe["instructions"] = full_recipe["instructions"][1:]

            enhanced.append(full_recipe)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ Done! Saved {len(enhanced)} recipes to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    run()
