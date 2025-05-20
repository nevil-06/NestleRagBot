# parse_flat_product_data.py
import json
import os
import re

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_product_data.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/structured_product_data.json")

SECTION_KEYS = ["features", "nutrition", "ingredients"]

def find_section_indices(raw, keys):
    anchors = []
    for i, line in enumerate(raw):
        for key in keys:
            if key in line.lower():
                anchors.append((key.lower(), i))
    return sorted(anchors, key=lambda x: x[1])

def extract_structured_fields(entry):
    raw = entry["raw_data"]
    data = {
        "url": entry["url"],
        "brand": entry["brand"],
        "category": entry["category"],
        "name": "",
        "weight": "",
        "description": "",
        "features_benefits": "",
        "nutrition": "",
        "ingredients": ""
    }

    # Extract name
    for line in raw:
        if len(line.split()) > 1 and all(x not in line.lower() for x in ["share", "facebook", "email", "twitter", "pinterest", "yum"]):
            data["name"] = line
            break

    # Extract weight
    for line in raw:
        if re.search(r"\b\d+(?:[.,]\d+)?\s?(g|kg|ml|l)\b", line, re.IGNORECASE):
            data["weight"] = line
            break

    # Section boundaries
    anchors = find_section_indices(raw, SECTION_KEYS)
    sections = {}
    for i, (label, start) in enumerate(anchors):
        end = anchors[i + 1][1] if i + 1 < len(anchors) else len(raw)
        section_lines = raw[start:end]

        # Handle inline "X: ..." or block after header
        if ":" in section_lines[0]:
            section_content = section_lines[0].split(":", 1)[1].strip()
        else:
            section_content = " ".join(section_lines[1:]).strip()

        sections[label] = section_content

    # Description = everything before first section header
    first_anchor = anchors[0][1] if anchors else len(raw)
    data["description"] = " ".join(raw[:first_anchor]).strip()

    # Assign sections
    data["features_benefits"] = sections.get("features", "")
    data["nutrition"] = sections.get("nutrition", "")
    data["ingredients"] = sections.get("ingredients", "")

    return data

def parse_all():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_entries = json.load(f)

    structured = [extract_structured_fields(entry) for entry in raw_entries]

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2)

    print(f"\n✅ Structured {len(structured)} products into structured_product_data.json")

if __name__ == "__main__":
    parse_all()
