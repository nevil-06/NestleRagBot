import os
import json
import pandas as pd
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

BASE_URL = "https://www.madewithnestle.ca/"
DOMAIN = urlparse(BASE_URL).netloc
VISITED = set()
SCRAPED_DATA = []

def extract_content(html, url):
    soup = BeautifulSoup(html, "lxml")
    return {
        "url": url,
        "title": soup.title.string if soup.title else "",
        "text": soup.get_text(separator=" ", strip=True),
        "links": [urljoin(url, a['href']) for a in soup.find_all('a', href=True)],
        "images": [urljoin(url, img['src']) for img in soup.find_all('img', src=True)],
        "tables": [str(table) for table in soup.find_all("table")],
    }

def is_internal_link(link):
    return urlparse(link).netloc in ("", DOMAIN)

def scrape_page(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_timeout(2000)
        page.mouse.wheel(0, 200)  # simulate scrolling
        page.wait_for_timeout(2000)
        return extract_content(page.content(), url)
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return None

def crawl_site(start_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)  # helpful for debugging
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            java_script_enabled=True,
            locale="en-US"
        )
        page = context.new_page()
        stealth_sync(page)  # 💡 Apply stealth here!

        queue = [start_url]
        while queue:
            url = queue.pop(0)
            if url in VISITED or not is_internal_link(url):
                continue
            VISITED.add(url)
            print(f"🔎 Scraping: {url}")
            content = scrape_page(page, url)
            if content:
                SCRAPED_DATA.append(content)
                for link in content['links']:
                    if is_internal_link(link) and link not in VISITED:
                        queue.append(link)

        browser.close()

def save_to_json(filename="nestle_scraped_data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(SCRAPED_DATA, f, ensure_ascii=False, indent=2)

def save_to_csv(filename="nestle_scraped_data.csv"):
    flat_data = [{"url": item["url"], "title": item["title"], "text": item["text"]} for item in SCRAPED_DATA]
    pd.DataFrame(flat_data).to_csv(filename, index=False)

if __name__ == "__main__":
    print("🚀 Starting crawl...")
    crawl_site(BASE_URL)
    print(f"\n✅ Scraped {len(SCRAPED_DATA)} pages")
    save_to_json()
    save_to_csv()
    print("📁 Data saved to disk.")
