from graph_query_engine import GraphQueryEngine
from dotenv import load_dotenv
import os

# Load credentials
load_dotenv()

# Initialize GraphQueryEngine for Cosmos DB (Gremlin API)
gqe = GraphQueryEngine(
    endpoint=os.getenv("COSMOS_ENDPOINT"),
    key=os.getenv("COSMOS_KEY"),
    database=os.getenv("COSMOS_DATABASE"),
    graph=os.getenv("COSMOS_GRAPH")
)

# Placeholder: replace this with actual vector search results
def dummy_vector_search(query):
    return [
        {"title": "Chocolate Cake", "score": 0.95},
        {"title": "Vanilla Cake", "score": 0.91},
    ]

# Combine graph and vector info
def graph_rag_retrieve(query):
    vector_results = dummy_vector_search(query)

    combined = []

    for doc in vector_results:
        title = doc["title"]
        ingredients = gqe.query_ingredients_for_product(title)
        combined.append({
            "title": title,
            "vector_score": doc["score"],
            "ingredients": ingredients
        })

    return combined

# ✅ Example usage
if __name__ == "__main__":
    query = "How do I make a chocolate cake?"
    results = graph_rag_retrieve(query)
    for item in results:
        print(f"\nRecipe: {item['title']}")
        print(f"Score: {item['vector_score']}")
        print("Ingredients from Graph:", item["ingredients"])

    gqe.close()
