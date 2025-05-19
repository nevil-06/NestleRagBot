# # scraper/scrape_recipe_details_bs4.py

# import requests
# from lxml import html
# import json
# import os
# import time

# INPUT_FILE = "data/nav_structure_labeled.json"
# OUTPUT_FILE = "data/recipe_details.json"

# HEADERS = {
#     "User-Agent": "Mozilla/5.0"
# }

# def extract_text_by_xpath(url):
#     try:
#         response = requests.get(url, headers=HEADERS, timeout=10)
#         response.raise_for_status()

#         tree = html.fromstring(response.content)

#         # Extract text from both recipe content blocks
#         block1 = tree.xpath('/html/body/div[2]/main/div/article/div[2]//text()')
#         block2 = tree.xpath('/html/body/div[2]/main/div/article/div[3]//text()')

#         full_text = " ".join(
#             text.strip() for text in (block1 + block2) if text.strip()
#         )

#         return {
#             "url": url,
#             "content": full_text
#         }

#     except Exception as e:
#         print(f"Failed to scrape {url}: {e}")
#         return None

# def load_recipe_urls(input_path):
#     with open(input_path, "r", encoding="utf-8") as f:
#         nav_data = json.load(f)

#     recipe_links = []

#     def collect_recipes(data):
#         for item in data:
#             if item.get("type") == "recipe" and item.get("url"):
#                 recipe_links.append(item["url"])
#             if "children" in item:
#                 collect_recipes(item["children"])

#     collect_recipes(nav_data)
#     return recipe_links

# def scrape_all_recipes():
#     recipe_urls = load_recipe_urls(INPUT_FILE)
#     print(f"Found {len(recipe_urls)} recipe URLs.")

#     all_recipes = []

#     for url in recipe_urls:
#         print(f"Scraping: {url}")
#         details = extract_text_by_xpath(url)
#         if details:
#             all_recipes.append(details)
#         time.sleep(1)  # Polite delay

#     os.makedirs("data", exist_ok=True)
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         json.dump(all_recipes, f, indent=2)

#     print(f"Saved {len(all_recipes)} recipes to {OUTPUT_FILE}")

# if __name__ == "__main__":
#     scrape_all_recipes()
