# recipe_scraper.py

import requests
from bs4 import BeautifulSoup
import json
import time

base_url = "https://www.madewithnestle.ca/recipes"
params = {"_wrapper_format": "html", "page": 0}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

all_recipes = []

while True:
    print(f"Fetching page {params['page']}...")
    response = requests.get(base_url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page {params['page']}. Status: {response.status_code}")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    recipe_links = soup.select('a.recipe-search-block[href]')

    if not recipe_links:
        print("No more recipes found.")
        break

    for tag in recipe_links:
        href = tag['href']
        url = href if href.startswith("http") else f"https://www.madewithnestle.ca{href}"

        title = tag.select_one('h4.coh-heading')
        desc = tag.select_one('.recipe-desc p')
        image = tag.select_one('.recipe-block-image img')
        prep_time = tag.select_one('.stat-prep-time')
        cook_time = tag.select_one('.stat-cook-time')

        recipe = {
            "title": title.get_text(strip=True) if title else None,
            "url": url,
            "description": desc.get_text(strip=True) if desc else None,
            "image": image['src'] if image and image.has_attr('src') else None,
            "prep_time_mins": int(prep_time.text.strip()) if prep_time else None,
            "cook_time_mins": int(cook_time.text.strip()) if cook_time else None
        }

        all_recipes.append(recipe)

    params["page"] += 1
    time.sleep(1)

# Save to JSON
with open("nestle_recipes.json", "w", encoding="utf-8") as f:
    json.dump(all_recipes, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(all_recipes)} recipes to 'nestle_recipes.json'")
