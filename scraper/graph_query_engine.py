from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin1234"


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
            RETURN DISTINCT r.title AS title, r.url AS url
            """
            result = session.run(query, product_name=product_name)
            return [record.data() for record in result]

    def get_products_used_in_recipe(self, recipe_title):
        with self.driver.session() as session:
            query = """
            MATCH (r:Recipe {title: $title})-[:USES_INGREDIENT]->(i)<-[:HAS_INGREDIENT]-(p:Product)
            RETURN DISTINCT p.name AS name, p.url AS url
            """
            result = session.run(query, title=recipe_title)
            return [record.data() for record in result]

    def get_related_ingredients(self, ingredient_name):
        with self.driver.session() as session:
            query = """
            MATCH (i:Ingredient)
            WHERE toLower(i.name) CONTAINS toLower($ingredient_name)
            OPTIONAL MATCH (r:Recipe)-[:USES_INGREDIENT]->(i)
            OPTIONAL MATCH (p:Product)-[:HAS_INGREDIENT]->(i)
            RETURN i.name AS ingredient,
                   collect(DISTINCT r.title) AS recipes,
                   collect(DISTINCT p.name) AS products
            """
            result = session.run(query, ingredient_name=ingredient_name)
            record = result.single()
            return record.data() if record else None

    def find_recipes_containing_similar_ingredient(self, product_name):
        with self.driver.session() as session:
            query = """
            MATCH (p:Product {name: $product_name})-[:HAS_INGREDIENT]->(i1)
            MATCH (r:Recipe)-[:USES_INGREDIENT]->(i2)
            WHERE toLower(i1.name) = toLower(i2.name)
            RETURN DISTINCT r.title AS title, r.url AS url
            LIMIT 10
            """
            result = session.run(query, product_name=product_name)
            return [record.data() for record in result]

    def get_recipe_by_title(self, title):
        with self.driver.session() as session:
            query = """
            MATCH (r:Recipe)
            WHERE toLower(r.title) CONTAINS toLower($title)
            RETURN r.title AS title, r.url AS url
            """
            result = session.run(query, title=title)
            return [record.data() for record in result]

    def get_product_by_name(self, name):
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)
            WHERE toLower(p.name) CONTAINS toLower($name)
            RETURN p.name AS name, p.url AS url
            """
            result = session.run(query, name=name)
            return [record.data() for record in result]

    def list_all_nodes_by_type(self, label):
        with self.driver.session() as session:
            query = f"""
            MATCH (n:{label})
            RETURN DISTINCT n.name AS name
            ORDER BY name
            LIMIT 100
            """
            result = session.run(query)
            return [record["name"] for record in result if record.get("name")]


# Optional test usage
if __name__ == "__main__":
    gq = GraphQueryEngine()

    print("\n🔍 Recipes using 'Aero':")
    print(gq.get_recipes_using_product("Aero"))

    print("\n🔍 Products in 'Nescafé Iced Coconut Latte':")
    print(gq.get_products_used_in_recipe("Nescafé Iced Coconut Latte"))

    print("\n🔍 Related to 'Coconut Milk':")
    print(gq.get_related_ingredients("Coconut Milk"))

    print("\n🔍 Recipes matching 'Truffle Salted':")
    print(gq.get_recipe_by_title("Truffle Salted"))

    print("\n🔍 Product lookup: 'Smarties':")
    print(gq.get_product_by_name("Smarties"))

    print("\n📋 All Ingredients (sample):")
    print(gq.list_all_nodes_by_type("Ingredient"))

    gq.close()
