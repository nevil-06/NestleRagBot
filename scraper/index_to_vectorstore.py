import os, re
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INPUT_PRODUCT_FILE = "data/structured_product_data.json"
INPUT_RECIPE_FILE = "data/full_nestle_recipes.json"
INDEX_FILE = "data/faiss_index_combined.bin"
METADATA_FILE = "data/faiss_metadata_combined.json"

MODEL_NAME = "all-MiniLM-L6-v2"

def build_vector_index():
    model = SentenceTransformer(MODEL_NAME)

    texts = []
    metadata = []
    seen_texts = set()

    # Load product data
    with open(INPUT_PRODUCT_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    for product in tqdm(products, desc="📦 Indexing products"):
        name = product.get("name", "")
        desc = product.get("description", "")
        features = product.get("features_benefits", "")
        ingredients = product.get("ingredients", "")

        chunks = [
            ("name_reference", f"This is about the product {name}."),
            ("overview", f"{name}. {desc}"),
            ("features", features),
            ("ingredients", ingredients),
        ]

        for chunk_type, text in chunks:
            if text and isinstance(text, str):
                clean_text = text.strip()
                if clean_text and clean_text.lower() not in seen_texts:
                    seen_texts.add(clean_text.lower())
                    texts.append(clean_text)
                    metadata.append({
                        "chunk_type": chunk_type,
                        "source": "product",
                        "product_name": name,
                        "brand": product.get("brand", ""),
                        "category": product.get("category", ""),
                        "url": product.get("url", ""),
                        "description": desc,
                        "features_benefits": features,
                        "weight": product.get("weight", ""),
                        "ingredients": ingredients,
                        "nutrition": product.get("nutrition", "")
                    })

    # Load recipe data
    with open(INPUT_RECIPE_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    for recipe in tqdm(recipes, desc="📖 Indexing recipes"):
        title = recipe.get("title", "")
        desc = recipe.get("description", "")
        ingredients_list = recipe.get("ingredients", [])
        instructions_list = recipe.get("instructions", [])

        ingredients = ", ".join(ingredients_list)
        instructions = " ".join(instructions_list)
        ing_summary = f"This recipe uses ingredients like: {ingredients[:150]}"

        chunks = [
            ("recipe_title", f"This recipe is titled: {title}"),
            ("recipe_description", desc),
            ("recipe_ingredients", ingredients),
            ("recipe_instructions", instructions),
            ("ingredient_summary", ing_summary)
        ]

        for chunk_type, text in chunks:
            if text and isinstance(text, str):
                clean_text = text.strip()
                if clean_text and clean_text.lower() not in seen_texts:
                    seen_texts.add(clean_text.lower())
                    texts.append(clean_text)
                    metadata.append({
                        "chunk_type": chunk_type,
                        "source": "recipe",
                        "recipe_title": title,
                        "prep_time": recipe.get("prep_time_mins", ""),
                        "cook_time": recipe.get("cook_time_mins", ""),
                        "servings": recipe.get("servings", ""),
                        "skill_level": recipe.get("skill_level", ""),
                        "url": recipe.get("url", "")
                    })

    # Load article/about page data (flat text style)
    ARTICLE_FILE = os.path.join(os.path.dirname(__file__), "../data/nestle_articles_detailed_cleaned.json")
    if os.path.exists(ARTICLE_FILE):
        with open(ARTICLE_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)

        for article in articles:
            title = article.get("title", "").strip()
            url = article.get("url", "").strip()
            desc = article.get("description", "").strip()
            body_raw = article.get("content", "").strip()
            # Clean raw content
            body_clean = re.sub(r"\n{2,}", "\n", body_raw)             # Collapse multiple newlines
            body_clean = re.sub(r"\t+", " ", body_clean)               # Replace tabs with space
            body_clean = re.sub(r"(LATEST|NUTRITION|Latest)", "", body_clean)  # Remove repeated headings
            body_clean = re.sub(r" +", " ", body_clean)                # Collapse multiple spaces

            text = f"{title}\n{desc}\n{body_clean}".strip()
            if len(text.strip()) > 20:
                texts.append(text)
                metadata.append({
                    "chunk_type": "article_full",
                    "source": "article",
                    "title": title,
                    "url": url,
                    "published": article.get("published", "")
                })
    else:
        logger.warning(f"❌ Article file not found: {ARTICLE_FILE}")

    logger.info("🧠 Encoding text chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    logger.info("📦 Creating FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✅ Indexed {len(texts)} unique chunks from products, recipes, and articles")
    logger.info(f"FAISS Index Size: {index.ntotal}")
    logger.info(f"Metadata Length: {len(metadata)}")

if __name__ == "__main__":
    build_vector_index()
