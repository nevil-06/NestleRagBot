from gremlin_python.driver import client, serializer
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

# Create Gremlin client for Azure Cosmos DB
g_client = client.Client(
    f"{os.getenv('COSMOS_ENDPOINT')}/gremlin",
    "g",
    username=f"/dbs/{os.getenv('COSMOS_DATABASE')}/colls/{os.getenv('COSMOS_GRAPH')}",
    password=os.getenv('COSMOS_KEY'),
    message_serializer=serializer.GraphSONSerializersV2d0()
)

# Example data
products = [
    {"id": "prod1", "name": "Chocolate Cake"},
    {"id": "prod2", "name": "Vanilla Cake"}
]

ingredients = [
    {"id": "ing1", "name": "Flour"},
    {"id": "ing2", "name": "Cocoa"},
    {"id": "ing3", "name": "Vanilla"}
]

edges = [
    ("prod1", "ing1", "USES"),
    ("prod1", "ing2", "USES"),
    ("prod2", "ing1", "USES"),
    ("prod2", "ing3", "USES")
]

# Add product nodes
for product in products:
    query = f"g.addV('Product')" \
            f".property('id', '{product['id']}')" \
            f".property('name', '{product['name']}')" \
            f".property('partitionKey', 'Product')"
    g_client.submit(query).all().result()

# Add ingredient nodes
for ingredient in ingredients:
    query = f"g.addV('Ingredient')" \
            f".property('id', '{ingredient['id']}')" \
            f".property('name', '{ingredient['name']}')" \
            f".property('partitionKey', 'Ingredient')"
    g_client.submit(query).all().result()

# Add edges
for from_id, to_id, label in edges:
    query = f"g.V('{from_id}').addE('{label}').to(g.V('{to_id}'))"
    g_client.submit(query).all().result()

# Close connection
g_client.close()
