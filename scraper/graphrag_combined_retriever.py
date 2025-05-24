import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

# Configs
INDEX_FILE = "data/faiss_index_combined.bin"
METADATA_FILE = "data/faiss_metadata_combined.json"
MODEL_NAME = "all-MiniLM-L6-v2"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Load index + metadata
faiss_index = faiss.read_index(INDEX_FILE)
with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

embed_model = SentenceTransformer(MODEL_NAME)

def vector_search(query, top_k=5):
    query_vec = embed_model.encode([query])
    D, I = faiss_index.search(np.array(query_vec).astype("float32"), top_k)

    results = []
    for i in I[0]:
        if i < len(metadata):
            results.append(metadata[i])
    return results

def graph_search(query, top_k=5):
    query_lower = query.lower()
    results = []

    with driver.session() as session:
        # Products
        product_results = session.run("""
            MATCH (p:Product)
            WHERE toLower(p.name) CONTAINS $q OR toLower(p.brand) CONTAINS $q
            RETURN p.name AS name, p.url AS url, p.description AS description
            LIMIT $top_k
        """, q=query_lower, top_k=top_k)

        for record in product_results:
            results.append({
                "source": "graph_product",
                "name": record["name"],
                "url": record["url"],
                "description": record["description"]
            })

        # Recipes connected to products
        recipe_results = session.run("""
            MATCH (p:Product)-[:MENTIONED_IN_INGREDIENT]->(r:Recipe)
            WHERE toLower(p.name) CONTAINS $q OR toLower(p.brand) CONTAINS $q
            RETURN DISTINCT r.title AS title, r.url AS url
            LIMIT $top_k
        """, q=query_lower, top_k=top_k)

        for record in recipe_results:
            results.append({
                "source": "graph_recipe",
                "title": record["title"],
                "url": record["url"]
            })

    return results

def detect_query_type(query: str) -> str:
    q = query.lower()
    if any(word in q for word in ["recipe", "cook", "bake", "make", "prepare"]):
        return "recipe"
    if any(word in q for word in ["product", "buy", "price", "brand", "category", "flavour", "flavor"]):
        return "product"
    return "both"

def combined_retrieve(query, top_k=5):
    print("🔍 Running combined retrieval...")
    intent = detect_query_type(query)
    print(f"🎯 Detected intent: {intent}")

    vector_results = vector_search(query, top_k)
    graph_results = graph_search(query, top_k)

    all_results = vector_results + graph_results

    if intent == "product":
        filtered = [r for r in all_results if r.get("source", "").startswith("product") or "product_name" in r]
    elif intent == "recipe":
        filtered = [r for r in all_results if r.get("source", "").startswith("recipe") or "recipe_title" in r]
    else:
        filtered = all_results

    print("\n✅ Filtered Results:")
    for r in filtered:
        label = r.get("name") or r.get("title") or r.get("product_name") or r.get("recipe_title")
        print(f"- {r['source']} → {label} → {r.get('url')}")

    return filtered
