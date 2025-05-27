from gremlin_python.driver import client, serializer

class GraphQueryEngine:
    def __init__(self, endpoint, key, database, graph):
        self.client = client.Client(
            f"{endpoint}/gremlin",
            "g",
            username=f"/dbs/{database}/colls/{graph}",
            password=key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

    def query_ingredients_for_product(self, product_name: str):
        gremlin_query = (
            f"g.V().has('Product', 'name', '{product_name}')"
            ".out('USES').hasLabel('Ingredient').values('name')"
        )
        return self.client.submit(gremlin_query).all().result()

    def query_related_products(self, ingredient_name: str):
        gremlin_query = (
            f"g.V().has('Ingredient', 'name', '{ingredient_name}')"
            ".in_('USES').hasLabel('Product').values('name')"
        )
        return self.client.submit(gremlin_query).all().result()

    def close(self):
        self.client.close()
