from gremlin_python.driver import client, serializer
from dotenv import load_dotenv
import os

load_dotenv()

class GraphQueryEngine:
    def __init__(self,
                 endpoint=os.getenv("COSMOS_ENDPOINT"),
                 key=os.getenv("COSMOS_KEY"),
                 database=os.getenv("COSMOS_DATABASE"),
                 graph=os.getenv("COSMOS_GRAPH")):
        self.client = client.Client(
            f"{endpoint}/gremlin",
            "g",
            username=f"/dbs/{database}/colls/{graph}",
            password=key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

    def close(self):
        self.client.close()

    def get_recipes_using_product(self, product_name):
        query = (
            f"g.V().hasLabel('Product').has('name', '{product_name}')"
            ".in_('USES').hasLabel('Recipe')"
            ".project('title','url').by(values('name')).by(values('url'))"
        )
        return self._run_query(query)

    def get_products_used_in_recipe(self, recipe_title):
        query = (
            f"g.V().hasLabel('Recipe').has('name', '{recipe_title}')"
            ".out('USES').hasLabel('Ingredient')"
            ".in_('USES').hasLabel('Product')"
            ".project('name','url').by(values('name')).by(values('url'))"
        )
        return self._run_query(query)

    def get_related_ingredients(self, ingredient_name):
        query = (
            f"g.V().hasLabel('Ingredient').has('name', '{ingredient_name}')"
            ".as('i')"
            ".in_('USES').hasLabel('Recipe').values('name').fold().as('recipes')"
            ".in_('USES').hasLabel('Product').values('name').fold().as('products')"
            ".select('i','recipes','products')"
        )
        results = self._run_query(query)
        if results and isinstance(results[0], dict):
            return {
                "ingredient": results[0].get('i', {}).get('name', ingredient_name),
                "recipes": results[0].get('recipes', []),
                "products": results[0].get('products', [])
            }
        return None

    def find_recipes_containing_similar_ingredient(self, product_name):
        query = (
            f"g.V().hasLabel('Product').has('name', '{product_name}')"
            ".out('USES').hasLabel('Ingredient').as('ing')"
            ".in_('USES').hasLabel('Recipe')"
            ".project('title','url').by(values('name')).by(values('url')).dedup()"
        )
        return self._run_query(query)

    def get_recipe_by_title(self, title):
        query = (
            f"g.V().hasLabel('Recipe').has('name', '{title}')"
            ".project('title','url').by(values('name')).by(values('url'))"
        )
        return self._run_query(query)

    def get_product_by_name(self, name):
        query = (
            f"g.V().hasLabel('Product').has('name', '{name}')"
            ".project('name','url').by(values('name')).by(values('url'))"
        )
        return self._run_query(query)

    def list_all_nodes_by_type(self, label):
        query = f"g.V().hasLabel('{label}').values('name').dedup().limit(100)"
        return self._run_query(query)

    def _run_query(self, gremlin_query):
        try:
            results = self.client.submit(gremlin_query).all().result()
            return results if results else []
        except Exception as e:
            print(f"⚠️ Gremlin Query Failed: {e}")
            return []
