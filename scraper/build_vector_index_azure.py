import os
import re
import json
from tqdm import tqdm
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# File paths
INPUT_PRODUCT_FILE = "data/structured_product_data.json"
INPUT_RECIPE_FILE = "data/full_nestle_recipes.json"
ARTICLE_FILE = "data/nestle_articles_detailed_cleaned.json"

# Azure Search setup
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="nestle-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

# OpenAI setup
embedding_model = "text-embedding-ada-002"

# Local embedding model (optional)
MODEL_NAME = "all-MiniLM-L6-v2"
local_model = SentenceTransformer(MODEL_NAME)

def create_embedding(text):
    response = client.embeddings.create(input=[text], model=embedding_model)
    return response.data[0].embedding

def build_vector_index():
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
                if clean_text.lower() not in seen_texts:
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

    # Load articles
    if os.path.exists(ARTICLE_FILE):
        with open(ARTICLE_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)

        for article in articles:
            title = article.get("title", "").strip()
            url = article.get("url", "").strip()
            desc = article.get("description", "").strip()
            body_raw = article.get("content", "").strip()

            body_clean = re.sub(r"\n{2,}", "\n", body_raw)
            body_clean = re.sub(r"\t+", " ", body_clean)
            body_clean = re.sub(r"(LATEST|NUTRITION|Latest)", "", body_clean)
            body_clean = re.sub(r" +", " ", body_clean)

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

    # Generate embeddings and upload to Azure
    logger.info("🧠 Uploading chunks to Azure Search...")
    documents = []
    for i, (text, meta) in enumerate(tqdm(zip(texts, metadata), total=len(texts))):
        embedding = create_embedding(text)
        doc = {
            "id": str(i + 1),
            "content": text,
            "embedding": embedding,
            **meta
        }
        documents.append(doc)

    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = search_client.upload_documents(documents=batch)
        logger.info(f"✅ Uploaded batch {i // batch_size + 1}: {result}")

    logger.info(f"🎉 Finished uploading {len(documents)} documents.")

if __name__ == "__main__":
    build_vector_index()
