import json
import re
from neo4j import GraphDatabase

# Load data
with open("data/structured_product_data.json", "r", encoding="utf-8") as f:
    products = json.load(f)

with open("data/full_nestle_recipes.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

# Neo4j config
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower()) if text else ""

def create_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")

    for product in products:
        tx.run("""
            MERGE (p:Product {name: $name})
            SET p.brand = $brand,
                p.category = $category,
                p.description = $description,
                p.features = $features,
                p.ingredients = $ingredients,
                p.url = $url
        """, name=product["name"],
             brand=product.get("brand", ""),
             category=product.get("category", ""),
             description=product.get("description", ""),
             features=product.get("features_benefits", ""),
             ingredients=product.get("ingredients", ""),
             url=product.get("url", ""))

        # Brand and Category nodes
        if product.get("brand"):
            tx.run("""
                MERGE (b:Brand {name: $brand})
                WITH b
                MATCH (p:Product {name: $name})
                MERGE (p)-[:IS_BRAND]->(b)
            """, name=product["name"], brand=product["brand"])

        if product.get("category"):
            tx.run("""
                MERGE (c:Category {name: $category})
                WITH c
                MATCH (p:Product {name: $name})
                MERGE (p)-[:IS_TYPE]->(c)
            """, name=product["name"], category=product["category"])

    for recipe in recipes:
        tx.run("""
            MERGE (r:Recipe {title: $title})
            SET r.url = $url,
                r.description = $description,
                r.skill_level = $skill_level,
                r.ingredients = $ingredients,
                r.instructions = $instructions
        """, title=recipe["title"],
             url=recipe["url"],
             description=recipe.get("description", ""),
             skill_level=recipe.get("skill_level", ""),
             ingredients=recipe.get("ingredients", []),
             instructions=recipe.get("instructions", []))

        for ing in recipe.get("ingredients", []):
            ing_clean = ing.strip()
            tx.run("""
                MERGE (i:Ingredient {name: $ing})
                WITH i
                MATCH (r:Recipe {title: $title})
                MERGE (i)-[:USED_IN]->(r)
            """, ing=ing_clean, title=recipe["title"])

    # Fuzzy product-ingredient mapping
    for product in products:
        pname = product["name"]
        pname_tokens = normalize(pname).split()
        pbrand = normalize(product.get("brand", ""))

        for recipe in recipes:
            matched = False
            for ing in recipe.get("ingredients", []):
                ing_norm = normalize(ing)

                if pbrand and pbrand in ing_norm:
                    matched = True
                elif any(token in ing_norm for token in pname_tokens):
                    matched = True

                if matched:
                    tx.run("""
                        MATCH (p:Product {name: $pname}), (r:Recipe {title: $rtitle})
                        MERGE (p)-[:MENTIONED_IN_INGREDIENT]->(r)
                    """, pname=pname, rtitle=recipe["title"])
                    break

def main():
    with driver.session() as session:
        print("📦 Building graph...")
        session.execute_write(create_graph)
        print("✅ Graph created!")

if __name__ == "__main__":
    main()
