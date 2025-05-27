from graph_query_engine import GraphQueryEngine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Cosmos DB Gremlin client
gqe = GraphQueryEngine(
    endpoint=os.getenv("COSMOS_ENDPOINT"),
    key=os.getenv("COSMOS_KEY"),
    database=os.getenv("COSMOS_DATABASE"),
    graph=os.getenv("COSMOS_GRAPH")
)

# 🔍 Example function: Get ingredients used in a product
def get_ingredients_for_product(product_name):
    try:
        return gqe.query_ingredients_for_product(product_name)
    except Exception as e:
        print(f"Error querying ingredients: {e}")
        return []

# 🔍 Example function: Get related products by ingredient
def get_related_products(ingredient_name):
    try:
        return gqe.query_related_products(ingredient_name)
    except Exception as e:
        print(f"Error querying related products: {e}")
        return []

# ✅ Example usage
if __name__ == "__main__":
    ingredients = get_ingredients_for_product("Chocolate Cake")
    print("Ingredients:", ingredients)

    related = get_related_products("Flour")
    print("Related products:", related)

    gqe.close()
