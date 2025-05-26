import json
import re

INPUT_FILE = "nestle_articles_detailed.json"
OUTPUT_FILE = "nestle_articles_detailed_cleaned.json"

JUNK_BLOCKS = [
    r"\bLATEST\b.*?(?=\n{2,}|$)",
    r"\bBRAND\b.*?(?=\n{2,}|$)",
    r"\bNUTRITION\b.*?(?=\n{2,}|$)"
]

def clean_text(text):
    # Remove predefined junk sections
    for pattern in JUNK_BLOCKS:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Replace all types of newlines (including \n\n, \n\t, etc.) with space
    text = re.sub(r"[\n\t\r]+", " ", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()



def clean_articles():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    for article in articles:
        article["content"] = clean_text(article["content"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"✅ Cleaned {len(articles)} articles. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_articles()
