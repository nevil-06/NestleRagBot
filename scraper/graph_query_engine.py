from neo4j import GraphDatabase

# Neo4j Desktop connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"  # ⬅️ Update this

class GraphQueryEngine:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_recipes_using_product(self, product_name):
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)-[:MENTIONED_IN_INGREDIENT]->(r:Recipe)
            WHERE toLower(p.name) CONTAINS toLower($product_name)
            RETURN r.title AS recipe, r.url AS url
            """
            result = session.run(query, product_name=product_name)
            return [{"recipe": r["recipe"], "url": r["url"]} for r in result]

    def get_products_used_in_recipe(self, recipe_title):
        query = """
        MATCH (r:Recipe {title: $recipe_title})-[:USES_INGREDIENT]->(i)<-[:HAS_INGREDIENT]-(p:Product)
        RETURN DISTINCT p.name AS product, p.url AS url
        LIMIT 10
        """
        with self.driver.session() as session:
            result = session.run(query, recipe_title=recipe_title)
            return [record.data() for record in result]

    def get_related_ingredients(self, ingredient_name):
        query = """
        MATCH (i:Ingredient {name: $ingredient_name})
        OPTIONAL MATCH (p:Product)-[:HAS_INGREDIENT]->(i)
        OPTIONAL MATCH (r:Recipe)-[:USES_INGREDIENT]->(i)
        RETURN DISTINCT i.name AS ingredient,
                        collect(DISTINCT p.name) AS products,
                        collect(DISTINCT r.title) AS recipes
        """
        with self.driver.session() as session:
            result = session.run(query, ingredient_name=ingredient_name)
            record = result.single()
            return record.data() if record else None
    
    def get_recipes_by_product_name(self, product_name):
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)-[:MENTIONED_IN_INGREDIENT]->(r:Recipe)
            WHERE toLower(p.name) CONTAINS toLower($product_name)
            RETURN r.title AS title, r.url AS url
            """
            result = session.run(query, product_name=product_name)
            return [{"title": r["title"], "url": r["url"]} for r in result]

# Example Usage
if __name__ == "__main__":
    engine = GraphQueryEngine()

    print("\n🔍 Recipes that use ingredients from 'AERO Scoops Vanilla Bean':")
    print(engine.get_recipes_using_product("AERO Scoops Vanilla Bean"))

    print("\n🔍 Products used in 'Nescafé Iced Coconut Latte':")
    print(engine.get_products_used_in_recipe("Nescafé Iced Coconut Latte"))

    print("\n🔍 Connections to ingredient 'Coconut Milk':")
    print(engine.get_related_ingredients("Coconut Milk"))

    engine.close()
