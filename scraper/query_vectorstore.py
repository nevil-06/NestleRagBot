# query_vectorstore.py

import os
import json
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import minmax_scale
from nltk.tokenize import word_tokenize

INDEX_FILE = os.path.join(os.path.dirname(__file__), "../data/faiss_index.bin")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "../data/faiss_metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5
ALPHA = 0.6  # Weight for BM25
BETA = 0.4   # Weight for Semantic

def load_data():
    print("📦 Loading index, metadata and model...")
    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE) as f:
        metadata = json.load(f)
    model = SentenceTransformer(MODEL_NAME)

    # For BM25: create a text corpus from metadata
    corpus = []
    for item in metadata:
        combined = " ".join([item["name"], item["brand"], item["category"]])
        corpus.append(word_tokenize(combined.lower()))
    bm25 = BM25Okapi(corpus)

    return index, metadata, model, bm25, corpus

def search(query, index, metadata, model, bm25, corpus):
    print(f"\n🔍 Query: {query}")
    query_tokens = word_tokenize(query.lower())
    bm25_scores = bm25.get_scores(query_tokens)

    # Get semantic scores from FAISS
    query_vec = model.encode([query])
    _, sem_indices = index.search(np.array(query_vec).astype("float32"), len(metadata))

    sem_scores = np.zeros(len(metadata))
    for rank, idx in enumerate(sem_indices[0]):
        sem_scores[idx] = 1 / (1 + rank)  # Higher rank = higher score

    # Normalize scores to 0-1
    bm25_norm = minmax_scale(bm25_scores)
    sem_norm = minmax_scale(sem_scores)

    final_scores = ALPHA * bm25_norm + BETA * sem_norm
    top_indices = np.argsort(final_scores)[::-1][:TOP_K]

    for rank, idx in enumerate(top_indices):
        item = metadata[idx]
        print(f"\n🔹 Result {rank + 1}")
        print(f"   Name: {item['name']}")
        print(f"   Brand: {item['brand']}")
        print(f"   Category: {item['category']}")
        print(f"   URL: {item['url']}")
        print(f"   Hybrid Score: {final_scores[idx]:.4f}")

if __name__ == "__main__":
    import nltk
    nltk.download("punkt")

    index, metadata, model, bm25, corpus = load_data()

    while True:
        query = input("\nType your product query (or 'exit' to quit): ").strip()
        if query.lower() in ["exit", "quit"]:
            break
        search(query, index, metadata, model, bm25, corpus)
