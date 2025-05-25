from neo4j import GraphDatabase

# Neo4j Desktop connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"  # ✅ Use secure handling in production


class GraphQueryEngine:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_recipes_using_product(self, product_name_or_brand):
        """
        Get recipes mentioning this product (match by name or brand substring).
        """
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)-[:MENTIONED_IN_INGREDIENT]->(r:Recipe)
            WHERE toLower(p.name) CONTAINS toLower($q) OR toLower(p.brand) CONTAINS toLower($q)
            RETURN DISTINCT r.title AS title, r.url AS url
            LIMIT 10
            """
            result = session.run(query, q=product_name_or_brand)
            return [{"title": r["title"], "url": r["url"]} for r in result]

    def get_products_used_in_recipe(self, recipe_title):
        """
        Find any known products (linked via ingredient) used in the specified recipe.
        """
        with self.driver.session() as session:
            query = """
            MATCH (r:Recipe {title: $title})-[:USES_INGREDIENT]->(i)<-[:HAS_INGREDIENT]-(p:Product)
            RETURN DISTINCT p.name AS name, p.url AS url
            LIMIT 10
            """
            result = session.run(query, title=recipe_title)
            return [{"name": r["name"], "url": r["url"]} for r in result]

    def get_related_ingredients(self, ingredient_name):
        """
        Return a list of products and recipes that involve the specified ingredient.
        """
        with self.driver.session() as session:
            query = """
            MATCH (i:Ingredient)
            WHERE toLower(i.name) CONTAINS toLower($ingredient_name)
            OPTIONAL MATCH (p:Product)-[:HAS_INGREDIENT]->(i)
            OPTIONAL MATCH (r:Recipe)-[:USES_INGREDIENT]->(i)
            RETURN DISTINCT i.name AS ingredient,
                            collect(DISTINCT {product: p.name, url: p.url}) AS products,
                            collect(DISTINCT {recipe: r.title, url: r.url}) AS recipes
            """
            result = session.run(query, ingredient_name=ingredient_name)
            record = result.single()
            return record.data() if record else None

    def get_product_by_name_or_brand(self, query_text):
        """
        Find products by fuzzy name or brand match (used for entity disambiguation).
        """
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)
            WHERE toLower(p.name) CONTAINS toLower($q)
               OR toLower(p.brand) CONTAINS toLower($q)
            RETURN DISTINCT p.name AS name, p.url AS url
            LIMIT 10
            """
            result = session.run(query, q=query_text)
            return [{"name": r["name"], "url": r["url"]} for r in result]

    def get_recipes_by_ingredient_match(self, keyword):
        """
        Fetch recipes where the keyword appears in any ingredient.
        """
        with self.driver.session() as session:
            query = """
            MATCH (i:Ingredient)
            WHERE toLower(i.name) CONTAINS toLower($keyword)
            MATCH (r:Recipe)-[:USES_INGREDIENT]->(i)
            RETURN DISTINCT r.title AS title, r.url AS url
            LIMIT 10
            """
            result = session.run(query, keyword=keyword)
            return [{"title": r["title"], "url": r["url"]} for r in result]


# ✅ Test if needed
if __name__ == "__main__":
    engine = GraphQueryEngine()

    print("\n📎 Recipes that use AERO brand:")
    print(engine.get_recipes_using_product("AERO"))

    print("\n📎 Products in 'Nescafé Iced Dalgona Coffee':")
    print(engine.get_products_used_in_recipe("Nescafé Iced Dalgona Coffee"))

    print("\n📎 Things related to 'Coconut Milk':")
    print(engine.get_related_ingredients("Coconut Milk"))

    print("\n📎 Products by name or brand 'Smarties':")
    print(engine.get_product_by_name_or_brand("Smarties"))

    print("\n📎 Recipes using keyword 'caramel':")
    print(engine.get_recipes_by_ingredient_match("caramel"))

    engine.close()
