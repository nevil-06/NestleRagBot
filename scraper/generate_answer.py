# ✅ Updated generate_answer.py with safer JSON parsing
import os
import json
import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
from .rerank_crossencoder import rerank_with_crossencoder
from .graph_query_engine import GraphQueryEngine

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
graph_query = GraphQueryEngine()

INDEX_FILE = "data/faiss_index_combined.bin"
METADATA_FILE = "data/faiss_metadata_combined.json"
PRODUCT_FILE = "data/structured_product_data.json"
RECIPE_FILE = "data/full_nestle_recipes.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
    ALL_PRODUCTS = json.load(f)

with open(RECIPE_FILE, "r", encoding="utf-8") as f:
    ALL_RECIPES = json.load(f)

def load_index():
    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)
    return index, metadata

def lookup_full_data(meta):
    if meta["source"] == "product":
        return next((p for p in ALL_PRODUCTS if p["url"] == meta.get("url")), None)
    elif meta["source"] == "recipe":
        return next((r for r in ALL_RECIPES if r["url"] == meta.get("url")), None)
    return None

def build_context_block(full_data, meta, index):
    if meta["source"] == "product":
        related_recipes = graph_query.get_recipes_using_product(full_data.get("name", ""))
        related_section = ""
        if related_recipes:
            links = "\n".join(f"- [{r['title']}]({r['url']})" for r in related_recipes)
            related_section = f"\nRelated Recipes:\n{links}"

        return f"""
[{index}] {full_data.get("name", "")}
Brand: {full_data.get("brand", "")}
Category: {full_data.get("category", "")}
Weight: {full_data.get("weight", "")}
Description: {full_data.get("description", "")}
Features & Benefits: {full_data.get("features_benefits", "")}
Nutrition: {full_data.get("nutrition", "")}
Ingredients: {full_data.get("ingredients", "")}
URL: {full_data.get("url", "")}
{related_section}
""".strip()

    elif meta["source"] == "recipe":
        ingredients = full_data.get("ingredients", [])[:3]
        top_ingredients = ", ".join(ingredients)
        return f"""
[{index}] {full_data.get("title", "")}
Type: Recipe
Skill Level: {full_data.get("skill_level", "")}
Prep Time: {full_data.get("prep_time_mins", "")} min | Cook Time: {full_data.get("cook_time_mins", "")} min
Top Ingredients: {top_ingredients}
Instructions: {" ".join(full_data.get("instructions", []))[:300]}...
URL: {full_data.get("url", "")}
""".strip()

def build_prompt(query, reranked_entries):
    blocks = []
    for i, (score, meta) in enumerate(reranked_entries, start=1):
        full_data = lookup_full_data(meta)
        if full_data:
            blocks.append(build_context_block(full_data, meta, i))

    context = "\n\n".join(blocks)

    system_prompt = """
You are a helpful assistant for Nestlé Canada. When a user asks a question, use only the context provided to answer.

✅ Format your response as valid JSON:

{
  "summary": "<brief answer to user's question>",
  "items": [
    {
      "title": "...",
      "type": "product" or "recipe",
      "description": "...",
      "url": "...",
      "category": "...",
      "weight": "...",
      "nutrition": "...",
      "prep_time": "...",
      "cook_time": "...",
      "top_ingredients": ["..."]
    }
  ],
  "followups": ["<suggested question>", "..."]
}

📌 Guidelines:
- Do not use Markdown formatting
- No emojis or special characters
- Keep it short, clean, and structured
- Only use context
"""

    user_prompt = f"""
### Context:
{context}

### Question:
"{query}"

Use the JSON structure described in the system prompt.
""".strip()

    return system_prompt.strip(), user_prompt.strip()

def safe_json_parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            cleaned = re.sub(r',\s*([}\]])', r'\1', text)  # Remove trailing commas
            return json.loads(cleaned)
        except Exception:
            return {
                "summary": "Sorry, I couldn't parse the response.",
                "items": [],
                "followups": []
            }

def generate_answer(query):
    index, metadata = load_index()
    query_vec = model.encode([query])
    D, I = index.search(np.array(query_vec).astype("float32"), 50)

    faiss_candidates = []
    seen_urls = set()

    for idx in I[0]:
        if idx < len(metadata):
            meta = metadata[idx]
            meta["chunk_text"] = meta.get("chunk_type", "")
            faiss_candidates.append(meta)
            seen_urls.add(meta.get("url"))

    graph_candidates = []
    for product in ALL_PRODUCTS:
        if product["name"].lower() in query.lower():
            matches = graph_query.get_recipes_using_product(product["name"])
            for rec in matches:
                if rec["url"] not in seen_urls:
                    graph_candidates.append({
                        "source": "recipe",
                        "chunk_type": "graph_hint",
                        "recipe_title": rec["title"],
                        "url": rec["url"],
                        "chunk_text": rec["title"]
                    })
                    seen_urls.add(rec["url"])

    all_candidates = faiss_candidates + graph_candidates
    reranked = rerank_with_crossencoder(query, all_candidates, top_k=6)
    system_prompt, user_prompt = build_prompt(query, reranked)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=900,
    )

    return safe_json_parse(response.choices[0].message.content.strip())
