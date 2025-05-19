# import json
# import os

# # Determine type based on URL path
# def classify_link(url: str) -> str:
#     if not url:
#         return "unknown"
#     url = url.lower()
#     if "/recipe/" in url:
#         return "recipe"
#     elif "/brands/" in url:
#         return "brand"
#     elif "/product/" in url or "/products/" in url:
#         return "product"
#     elif "/tips-articles/" in url:
#         return "article"
#     elif "/collections/" in url:
#         return "collection"
#     else:
#         return "other"

# # Recursively add type to each nav item
# def label_nav_items(items: list):
#     for item in items:
#         url = item.get("url", "")
#         item["type"] = classify_link(url)
#         if "children" in item and isinstance(item["children"], list):
#             label_nav_items(item["children"])

# def main():
#     input_path = "data/nav_structure.json"
#     output_path = "data/nav_structure_labeled.json"

#     with open(input_path, "r", encoding="utf-8") as f:
#         nav_data = json.load(f)

#     label_nav_items(nav_data)

#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(nav_data, f, indent=2)

#     print(f"Labeled nav structure saved to: {output_path}")

# if __name__ == "__main__":
#     main()
