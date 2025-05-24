import json
import os
import re
from collections import OrderedDict

# SECTION HEADINGS TO LOCATE
SECTION_KEYS = ["features", "nutrition", "ingredients"]

def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.replace("’", "'")          # Curly apostrophe → straight
    text = text.replace("–", "-")          # En dash → hyphen
    text = re.sub(r"[®™‡*]", "", text)     # Remove special marks
    text = text.replace("\u200b", "")      # Zero-width space
    text = re.sub(r"\s+", " ", text)       # Collapse multiple spaces
    return text.strip()

def find_section_indices(lines, keys):
    result = []
    for i, line in enumerate(lines):
        for key in keys:
            if key.lower() in line.lower():
                result.append((key.lower(), i))
    return sorted(result, key=lambda x: x[1])

def extract_structured_fields(entry):
    raw = entry["raw_data"]
    data = {
        "url": entry["url"],
        "brand": clean_text(entry["brand"]),
        "category": clean_text(entry["category"]),
        "name": "",
        "weight": "",
        "description": "",
        "features_benefits": "",
        "nutrition": "",
        "ingredients": ""
    }

    # Use explicit ingredients if available
    if entry.get("explicit_ingredients"):
        data["ingredients"] = clean_text(", ".join(entry["explicit_ingredients"]))

    # Extract name
    for line in raw:
        if len(line.split()) > 1 and all(x not in line.lower() for x in ["share", "facebook", "email", "twitter", "pinterest", "yum"]):
            data["name"] = clean_text(line)
            break

    # Extract weight
    for line in raw:
        if re.search(r"\b\d+(?:[.,]\d+)?\s?(g|kg|ml|l)\b", line, re.IGNORECASE):
            data["weight"] = clean_text(line)
            break

    # Section parsing
    anchors = find_section_indices(raw, SECTION_KEYS)
    sections = {}
    for i, (label, start) in enumerate(anchors):
        end = anchors[i + 1][1] if i + 1 < len(anchors) else len(raw)
        section_lines = raw[start:end]

        if ":" in section_lines[0]:
            section_content = section_lines[0].split(":", 1)[1].strip()
        else:
            section_content = " ".join(section_lines[1:]).strip()

        sections[label] = section_content

    data["description"] = clean_text(" ".join(raw[:anchors[0][1]]).strip() if anchors else " ".join(raw).strip())
    data["features_benefits"] = clean_text(sections.get("features", ""))
    data["nutrition"] = clean_text(sections.get("nutrition", ""))

    # Only fallback to parsed ingredients if explicit was not used
    if not data["ingredients"]:
        data["ingredients"] = clean_text(sections.get("ingredients", ""))

    return data

def parse_all_products():
    with open("data/full_product_data.json", "r", encoding="utf-8") as f:
        raw_products = json.load(f)

    structured = []
    for entry in raw_products:
        structured.append(extract_structured_fields(entry))

    os.makedirs("data", exist_ok=True)
    with open("data/structured_product_data.json", "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)

    print(f"✅ Parsed and cleaned {len(structured)} products.")

if __name__ == "__main__":
    parse_all_products()
