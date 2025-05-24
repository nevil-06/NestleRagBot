import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
from .rerank_crossencoder import rerank_with_crossencoder

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

INDEX_FILE = "data/faiss_index_combined.bin"
METADATA_FILE = "data/faiss_metadata_combined.json"
model = SentenceTransformer("all-MiniLM-L6-v2")

def load_index():
    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE) as f:
        metadata = json.load(f)
    return index, metadata

def build_prompt(query, top_chunks):
    blocks = []

    for meta in [item[1] for item in top_chunks]:
        if meta["source"] == "product":
            block = (
                f"- [{meta.get('product_name')}]({meta.get('url')})\n"
                f"  - Brand: {meta.get('brand', '')}\n"
                f"  - Category: {meta.get('category', '')}\n"
                f"  - Description: {meta.get('description', '')}\n"
                f"  - Features: {meta.get('features_benefits', '')}\n"
                f"  - Weight: {meta.get('weight', '')}"
            )
            blocks.append(block)
        else:
            block = (
                f"- [{meta.get('recipe_title')}]({meta.get('url')})\n"
                f"  - Skill Level: {meta.get('skill_level', '')}\n"
                f"  - Prep Time: {meta.get('prep_time', 'N/A')} mins\n"
                f"  - Cook Time: {meta.get('cook_time', 'N/A')} mins\n"
                f"  - Servings: {meta.get('servings', '')}"
            )
            blocks.append(block)

    context = "\n\n".join(blocks)

    system_prompt = """
You are a helpful assistant answering questions about Nestlé products and recipes.

- If the query is about a product (e.g., "Is Aero gluten free?"), use product information only.
- If the query is about recipes (e.g., "How do I make mocha with Carnation?"), use recipe information only.
- If the user asks if a product contains an ingredient, answer precisely based on product data.
- Do not mention both recipes and products unless the question asks for both.
- Use proper markdown-style hyperlinks like [Product Name](url). Do not use 'View →' or numeric references.

Answer clearly and concisely.
"""

    user_prompt = f"""Context:

{context}

Q: {query}
A:"""

    return system_prompt.strip(), user_prompt.strip()

def generate_answer(query):
    index, metadata = load_index()
    query_vec = model.encode([query])
    scores, indices = index.search(np.array(query_vec).astype("float32"), 50)

    candidates = []
    for idx in indices[0]:
        meta = metadata[idx]
        meta["chunk_text"] = meta.get("chunk_type", "")
        candidates.append(meta)

    reranked = rerank_with_crossencoder(query, candidates, top_k=5)
    system, user = build_prompt(query, reranked)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
        max_tokens=700,
    )

    return response.choices[0].message.content.strip()
