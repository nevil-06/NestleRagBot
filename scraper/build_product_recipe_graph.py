import json
from neo4j import GraphDatabase
from difflib import SequenceMatcher

# File paths
PRODUCT_FILE = "data/structured_product_data.json"
RECIPE_FILE = "data/full_nestle_recipes.json"

# Neo4j credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Load JSON
with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

with open(RECIPE_FILE, "r", encoding="utf-8") as f:
    recipes = json.load(f)


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def create_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")  # Clear DB

    # Create Product nodes
    for product in products:
        tx.run(
            """
            MERGE (p:Product {
                name: $name,
                brand: $brand,
                category: $category,
                url: $url,
                description: $description
            })
        """,
            name=product["name"],
            brand=product.get("brand", ""),
            category=product.get("category", ""),
            url=product.get("url", ""),
            description=product.get("description", ""),
        )

    # Create Recipe nodes
    for recipe in recipes:
        tx.run("""
            MERGE (r:Recipe {title: $title, url: $url})
            SET r.skill_level = $skill_level,
                r.prep_time = $prep_time,
                r.cook_time = $cook_time,
                r.servings = $servings
        """, title=recipe["title"],
             url=recipe["url"],
             skill_level=recipe.get("skill_level"),
             prep_time=recipe.get("prep_time_mins"),
             cook_time=recipe.get("cook_time_mins"),
             servings=recipe.get("servings"))


        for ingredient in recipe.get("ingredients", []):
            tx.run(
                """
                MERGE (i:Ingredient {name: $name})
                WITH i
                MATCH (r:Recipe {title: $recipe_title})
                MERGE (r)-[:USES_INGREDIENT]->(i)
            """,
                name=ingredient.strip(),
                recipe_title=recipe["title"],
            )

    # Link Products to Ingredients
    for product in products:
        name = product["name"]
        brand = product.get("brand", "")
        ingredients_text = product.get("ingredients", "")
        for raw_ingredient in ingredients_text.split(","):
            ingredient = raw_ingredient.strip()
            if ingredient:
                tx.run(
                    """
                    MERGE (i:Ingredient {name: $name})
                    WITH i
                    MATCH (p:Product {name: $product_name})
                    MERGE (p)-[:HAS_INGREDIENT]->(i)
                """,
                    name=ingredient,
                    product_name=name,
                )

    # Create fuzzy MENTIONED_IN_INGREDIENT links
    for recipe in recipes:
        recipe_title = recipe["title"]
        for recipe_ing in recipe.get("ingredients", []):
            ing_lc = recipe_ing.lower()
            for product in products:
                prod_name = product["name"]
                brand = product.get("brand", "")
                if (
                    brand
                    and brand.lower() in ing_lc
                    or any(token in ing_lc for token in prod_name.lower().split())
                ):
                    tx.run(
                        """
                        MATCH (p:Product {name: $product_name})
                        MATCH (r:Recipe {title: $recipe_title})
                        MERGE (p)-[:MENTIONED_IN_INGREDIENT]->(r)
                    """,
                        product_name=prod_name,
                        recipe_title=recipe_title,
                    )


def main():
    with driver.session() as session:
        print("🔄 Rebuilding graph...")
        session.execute_write(create_graph)
        print("✅ Graph updated with products, ingredients, and recipes")


if __name__ == "__main__":
    main()
