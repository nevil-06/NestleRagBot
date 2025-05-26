import json
from neo4j import GraphDatabase
from difflib import get_close_matches

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

# Build ingredient lookup from products
PRODUCT_ING_MAP = {}
ALL_INGREDIENTS = set()

for product in products:
    prod_name = product["name"]
    prod_ings = [
        ing.strip().lower()
        for ing in product.get("ingredients", "").split(",")
        if ing.strip()
    ]
    PRODUCT_ING_MAP[prod_name] = prod_ings
    ALL_INGREDIENTS.update(prod_ings)


def create_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")  # Clear DB

    # Product nodes
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

    # Recipe nodes + ingredients
    for recipe in recipes:
        tx.run(
            """
            MERGE (r:Recipe {title: $title, url: $url})
            SET r.skill_level = $skill_level,
                r.prep_time = $prep_time,
                r.cook_time = $cook_time,
                r.servings = $servings
            """,
            title=recipe["title"],
            url=recipe["url"],
            skill_level=recipe.get("skill_level"),
            prep_time=recipe.get("prep_time_mins", 0),
            cook_time=recipe.get("cook_time_mins", 0),
            servings=recipe.get("servings", 0),
        )

        for ing in recipe.get("ingredients", []):
            ing_clean = ing.strip().lower()
            tx.run(
                """
                MERGE (i:Ingredient {name: $name})
                WITH i
                MATCH (r:Recipe {title: $recipe_title})
                MERGE (r)-[:USES_INGREDIENT]->(i)
                """,
                name=ing_clean,
                recipe_title=recipe["title"],
            )

    # Product to ingredient links
    for product in products:
        pname = product["name"]
        for ing in PRODUCT_ING_MAP[pname]:
            tx.run(
                """
                MERGE (i:Ingredient {name: $ing})
                WITH i
                MATCH (p:Product {name: $pname})
                MERGE (p)-[:HAS_INGREDIENT]->(i)
                """,
                ing=ing,
                pname=pname,
            )

    # Fuzzy ingredient linking: MENTIONED_IN_INGREDIENT
    for recipe in recipes:
        recipe_title = recipe["title"]
        for recipe_ing in recipe.get("ingredients", []):
            rec_ing_norm = recipe_ing.strip().lower()
            match = get_close_matches(rec_ing_norm, ALL_INGREDIENTS, n=1, cutoff=0.85)
            if match:
                matched_ing = match[0]
                for pname, ing_list in PRODUCT_ING_MAP.items():
                    if matched_ing in ing_list:
                        tx.run(
                            """
                            MATCH (p:Product {name: $pname})
                            MATCH (r:Recipe {title: $rname})
                            MERGE (p)-[:MENTIONED_IN_INGREDIENT]->(r)
                            """,
                            pname=pname,
                            rname=recipe_title,
                        )


def main():
    print("🔄 Rebuilding graph...")
    with driver.session() as session:
        session.execute_write(create_graph)
    print("✅ Graph updated with improved fuzzy links.")


if __name__ == "__main__":
    main()
