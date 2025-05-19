import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/structured_product_data.json")
INDEX_FILE = os.path.join(os.path.dirname(__file__), "../data/faiss_index.bin")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "../data/faiss_metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"

def build_vector_index():
    with open(INPUT_FILE) as f:
        products = json.load(f)

    model = SentenceTransformer(MODEL_NAME)

    texts = []
    metadata = []

    for product in products:
        name = product.get("name", "")
        brand = product.get("brand", "")
        category = product.get("category", "")
        url = product.get("url", "")

        chunks = [
            ("overview", f"{name}. {product.get('description', '')}"),
            ("features", product.get("features_benefits", "")),
            ("ingredients", product.get("ingredients", ""))
        ]

        for chunk_type, text in chunks:
            if text.strip():
                texts.append(text.strip())
                metadata.append({
                    "chunk_type": chunk_type,
                    "product_name": name,
                    "brand": brand,
                    "category": category,
                    "url": url
                })

    print("🧠 Encoding text chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    print("📦 Creating FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Indexed {len(texts)} chunks across {len(products)} products")

if __name__ == "__main__":
    build_vector_index()
