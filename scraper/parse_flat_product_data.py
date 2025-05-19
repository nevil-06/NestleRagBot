# parse_flat_product_data.py

import json
import os
import re

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/full_product_data.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/structured_product_data.json")

def find_all_indices(raw, keyword):
    return [i for i, line in enumerate(raw) if keyword.lower() in line.lower()]

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

    # Name
    name_candidates = [line for line in raw if len(line.split()) > 1 and line.lower() not in ["share this", "facebook", "twitter", "pinterest", "email", "yum", "share"]]
    if name_candidates:
        data["name"] = name_candidates[0]

    # Weight
    for line in raw:
        if re.search(r"\b\d+(?:[.,]\d+)?\s?(g|kg|ml|l)\b", line, re.IGNORECASE):
            data["weight"] = line
            break

    # Section markers
    idx_feat_all = find_all_indices(raw, "features")
    idx_nutrition_all = find_all_indices(raw, "nutrition")
    idx_ingredients_all = find_all_indices(raw, "ingredient")

    idx_feat = idx_feat_all[0] if idx_feat_all else -1
    idx_nutrition = next((i for i in idx_nutrition_all if i > idx_feat), -1)
    idx_ingredients = next(
        (i for i in idx_ingredients_all if i > idx_nutrition),
        idx_ingredients_all[-1] if idx_ingredients_all else -1
    )

    print(f"\n→ {entry['url']}")
    print(f"   Found Features at {idx_feat}, Nutrition at {idx_nutrition}, Ingredients at {idx_ingredients}")

    # Description
    cutoff = min([i for i in [idx_feat, idx_nutrition, idx_ingredients] if i > 0], default=len(raw))
    data["description"] = " ".join(raw[:cutoff]).strip()

    # Features
    if 0 <= idx_feat < idx_nutrition or (idx_feat >= 0 and idx_nutrition == -1):
        end = idx_nutrition if idx_nutrition > idx_feat else len(raw)
        features = raw[idx_feat+1:end]
        data["features_benefits"] = " ".join(features).strip()

    # Nutrition
    if 0 <= idx_nutrition < idx_ingredients or (idx_nutrition >= 0 and idx_ingredients == -1):
        end = idx_ingredients if idx_ingredients > idx_nutrition else len(raw)
        nutrition = raw[idx_nutrition+1:end]
        data["nutrition"] = " ".join(nutrition).strip()

    # Ingredients (inline or following lines)
    if idx_ingredients >= 0:
        line = raw[idx_ingredients]
        if ":" in line:
            data["ingredients"] = line.split(":", 1)[1].strip()
        else:
            ingredients = raw[idx_ingredients+1:]
            data["ingredients"] = " ".join(ingredients).strip()

    return data

def parse_all():
    with open(INPUT_FILE) as f:
        raw_entries = json.load(f)

    structured = [extract_structured_fields(entry) for entry in raw_entries]

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(structured, f, indent=2)

    print(f"\n✅ Structured {len(structured)} products into structured_product_data.json")

if __name__ == "__main__":
    parse_all()
