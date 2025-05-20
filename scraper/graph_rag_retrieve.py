# graph_rag_retrieve.py

import os
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import minmax_scale

INDEX_FILE = "data/faiss_index.bin"
METADATA_FILE = "data/faiss_metadata.json"
GRAPH_FILE = "data/product_graph.gpickle"
STRUCTURED_FILE = "data/structured_product_data.json"

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5
COMMON_INGREDIENTS = {
    "sugar", "salt", "milk", "water", "cocoa", "glucose", "lecithin", "natural flavour"
}

def load_all():
    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE) as f:
        meta = json.load(f)
    with open(STRUCTURED_FILE) as f:
        structured = json.load(f)
    with open(GRAPH_FILE, "rb") as f:
        G = pickle.load(f)
    model = SentenceTransformer(MODEL_NAME)
    return index, meta, structured, G, model

def get_structured_by_name(name, structured):
    for item in structured:
        if item["name"].lower().strip() == name.lower().strip():
            return item
    return {}

def rerank_score(meta, main_struct, graph):
    score = 0.0
    # Match brand
    if meta["brand"] == main_struct["brand"]:
        score += 0.3
    # Match category
    if meta["category"] == main_struct["category"]:
        score += 0.3
    # Shared rare ingredient
    if meta["product_name"] in graph and main_struct["name"] in graph:
        ingredients = [n for n in graph.successors(meta["product_name"]) if graph.nodes[n]["type"] == "Ingredient"]
        query_ings = [n for n in graph.successors(main_struct["name"]) if graph.nodes[n]["type"] == "Ingredient"]
        shared = set(ingredients).intersection(query_ings) - COMMON_INGREDIENTS
        if shared:
            score += 0.4
    return score

def assemble_context(name, structured, graph):
    prod = get_structured_by_name(name, structured)
    if not prod:
        return "⚠️ No structured data found"

    context = f"🧾 Product: {prod['name']}\nBrand: {prod['brand']}\nCategory: {prod['category']}\n\n"
    context += f"Description:\n{prod.get('description', '')}\n\n"
    context += f"Features:\n{prod.get('features_benefits', '')}\n\n"
    context += f"Ingredients:\n{prod.get('ingredients', '')}\n\n"
    return context

def graph_reranked_top_products(query, top_n=3, return_data=False):
    index, metadata, structured, G, model = load_all()

    query_vec = model.encode([query])
    scores, indices = index.search(np.array(query_vec).astype("float32"), 50)

    semantic_scores = scores[0]
    semantic_norm = minmax_scale(-semantic_scores)

    reranked = []
    main_name = metadata[indices[0][0]]["product_name"]
    main_struct = get_structured_by_name(main_name, structured)

    for i, idx in enumerate(indices[0]):
        meta = metadata[idx]
        semantic_score = semantic_norm[i]
        boost = rerank_score(meta, main_struct, G)
        final_score = 0.6 * semantic_score + 0.4 * boost

        reranked.append((final_score, meta))

    # Deduplicate by product_name
    seen = set()
    unique_products = []
    for score, meta in sorted(reranked, key=lambda x: x[0], reverse=True):
        pname = meta["product_name"]
        if pname not in seen:
            seen.add(pname)
            unique_products.append((score, meta))
        if len(unique_products) == top_n:
            break

    if return_data:
        return unique_products

    # CLI output if not returning data
    print(f"\n🔍 Query: {query}")
    print(f"Top {top_n} distinct products:\n")
    for i, (score, meta) in enumerate(unique_products):
        print(f"🔹 Rank {i+1} | Score: {score:.4f}")
        print(f"   Product: {meta['product_name']}")
        print(f"   Brand: {meta['brand']}")
        print(f"   Category: {meta['category']}")
        print(f"   URL: {meta['url']}")
        print("-" * 50)


if __name__ == "__main__":
    while True:
        q = input("\nEnter product query (or 'exit'): ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        graph_reranked_top_products(q)
