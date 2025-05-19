# import os
# import json
# import time
# from urllib.parse import urljoin
# from playwright.sync_api import sync_playwright

# BASE_URL = "https://www.madewithnestle.ca/"
# OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/recipes_list.json")

# def discover_recipe_links_playwright():
#     results = []

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False, slow_mo=100)
#         page = browser.new_page()
#         page.goto(BASE_URL)
#         page.wait_for_load_state("networkidle")
#         time.sleep(1)

#         # Accept cookies
#         try:
#             page.click("button:has-text('Accept')", timeout=5000)
#             print("✅ Accepted cookies")
#         except:
#             print("⚠️ No cookie popup")

#         # Hover over 'All recipes'
#         try:
#             page.hover("nav >> text=All recipes")
#             time.sleep(1)
#             print("✅ Hovered on 'All recipes'")
#         except Exception as e:
#             page.screenshot(path="debug_all_recipes.png")
#             print(f"❌ Failed to hover on 'All recipes': {e}")
#             return

#         # Get all subcategories (e.g., A World of Flavours)
#         submenus = page.query_selector_all(".menu-level-2-ul > li")
#         print(f"🔎 Found {len(submenus)} recipe categories")

#         for submenu in submenus:
#             try:
#                 title = submenu.inner_text().strip().split("\n")[0]
#                 submenu.hover()
#                 time.sleep(1)

#                 # Get recipe links from left panel
#                 links = submenu.query_selector_all(".menu-level-3-ul a")
#                 for link in links:
#                     label = link.inner_text().strip()
#                     href = link.get_attribute("href")
#                     if href and label:
#                         results.append({
#                             "category": title,
#                             "title": label,
#                             "url": urljoin(BASE_URL, href)
#                         })
#             except Exception as e:
#                 print(f"❌ Failed to parse category: {e}")

#         browser.close()

#     os.makedirs("data", exist_ok=True)
#     with open(OUTPUT_FILE, "w") as f:
#         json.dump(results, f, indent=2)

#     print(f"\n✅ Saved {len(results)} recipes to recipes_list.json")

# if __name__ == "__main__":
#     discover_recipe_links_playwright()
