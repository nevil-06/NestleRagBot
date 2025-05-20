# recipe_full_details.py

import json
import requests
from bs4 import BeautifulSoup
import time
from collections import OrderedDict


# Load original recipes file
with open("data/nestle_recipes.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
def extract_full_recipe(url):
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Failed to fetch: {url}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Title (optional redundancy check)
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Description
        desc = soup.select_one(".recipe-desc p")
        description = desc.get_text(strip=True) if desc else None

        # Prep and Cook Time
        prep = soup.select_one(".stat-prep-time")
        cook = soup.select_one(".stat-cook-time")
        prep_time = int(prep.text.strip()) if prep and prep.text.strip().isdigit() else None
        cook_time = int(cook.text.strip()) if cook and cook.text.strip().isdigit() else None

        # Servings
        serving_tag = soup.select_one("span.serving-value.value")
        servings = int(serving_tag.get_text(strip=True)) if serving_tag else None

        # Skill Level
        skill_tag = soup.select_one("span.skill-level-value.value")
        skill_level = skill_tag.get_text(strip=True) if skill_tag else None

        # Ingredients
        ingredients = [
            tag.get_text(strip=True)
            for tag in soup.select("div.field--name-field-ingredient-fullname.field__item")
            if tag.get_text(strip=True)
        ]
        ingredients = list(OrderedDict.fromkeys(ingredients)) if ingredients else None

        # Instructions
        raw_steps = [
            p.get_text(strip=True)
            for p in soup.select("article p.coh-paragraph")
            if p.get_text(strip=True)
        ]
        seen = OrderedDict()
        for step in raw_steps:
            if step not in seen:
                seen[step] = None
        instructions = list(seen.keys())

        # Optionally drop intro paragraph
        if instructions and "chocolatier" in instructions[0].lower():
            instructions = instructions[1:]

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
        print(f"Error at {url}: {e}")
        return None



# Enhance each recipe with extra fields
enhanced = []
for recipe in recipes:
    print(f"Scraping: {recipe['title']}")
    details = extract_full_recipe(recipe["url"])
    time.sleep(1)

    if details:
        full_recipe = {
            "title": recipe["title"],
            "description": details["description"] or recipe.get("description"),
            "prep_time_mins": details["prep_time_mins"] or recipe.get("prep_time_mins"),
            "cook_time_mins": details["cook_time_mins"] or recipe.get("cook_time_mins"),
            "servings": details["servings"],
            "skill_level": details["skill_level"],
            "ingredients": details["ingredients"],
            "instructions": details["instructions"],
            "url": recipe["url"]
        }
        enhanced.append(full_recipe)

# Save to file
with open("data/full_nestle_recipes.json", "w", encoding="utf-8") as f:
    json.dump(enhanced, f, ensure_ascii=False, indent=2)

print(f"\n✅ Done! Saved {len(enhanced)} recipes to 'data/clearfull_nestle_recipes.json'")
