import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
from .rerank_crossencoder import rerank_with_crossencoder
from .graph_query_engine import GraphQueryEngine  # NEW IMPORT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
graph_query = GraphQueryEngine()
# File paths
INDEX_FILE = "data/faiss_index_combined.bin"
METADATA_FILE = "data/faiss_metadata_combined.json"
PRODUCT_FILE = "data/structured_product_data.json"
RECIPE_FILE = "data/full_nestle_recipes.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load JSON once
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
        return next((p for p in ALL_PRODUCTS if p["url"] == meta["url"]), None)
    else:
        return next((r for r in ALL_RECIPES if r["url"] == meta["url"]), None)



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
"""
    else:
        return f"""
[{index}] {full_data.get("title", "")}
Type: Recipe
Skill Level: {full_data.get("skill_level", "")}
Prep Time: {full_data.get("prep_time_mins", "")} min | Cook Time: {full_data.get("cook_time_mins", "")} min
Ingredients: {", ".join(full_data.get("ingredients", []))}
Instructions: {" ".join(full_data.get("instructions", []))[:300]}...
URL: {full_data.get("url", "")}
"""


def build_prompt(query, reranked_entries):
    blocks = []
    for i, (score, meta) in enumerate(reranked_entries, start=1):
        full_data = lookup_full_data(meta)
        if full_data:
            blocks.append(build_context_block(full_data, meta, i))
    context = "\n".join(blocks)

    system_prompt = """
You are a helpful assistant answering questions about Nestlé products and recipes.

🔎 Retrieval Scope:
- Only use data from the official Canadian Nestlé website (madewithnestle.ca).
- Do NOT generate or mention products from other countries.
- Do not hallucinate recipes or instructions not present in the context.

🔍 Logic:
- If the question is about a product, only use product information.
- If the question is about a recipe, only use recipe information.
- If the user asks about ingredients in a product, respond precisely from the ingredient list.
- Do not mix product and recipe info unless the user explicitly asks about both.

📦 Format:
- Start with a short, informative answer.
- If relevant, list matching items with names and clickable URLs.
- Example: 
  - [AERO Truffle Salted Caramel](https://www.madewithnestle.ca/aero/aero-truffle-salted-caramel)
"""

    user_prompt = f"""
### Context:
{context}

### Question:
"{query}"
""".strip()

    return system_prompt, user_prompt


def generate_answer(query):
    index, metadata = load_index()
    query_vec = model.encode([query])
    D, I = index.search(np.array(query_vec).astype("float32"), 50)

    candidates = []
    for idx in I[0]:
        if idx < len(metadata):
            meta = metadata[idx]
            meta["chunk_text"] = meta.get("chunk_type", "")  # Required for reranker
            candidates.append(meta)

    reranked = rerank_with_crossencoder(query, candidates, top_k=5)
    system_prompt, user_prompt = build_prompt(query, reranked)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=700,
    )

    return response.choices[0].message.content.strip()
