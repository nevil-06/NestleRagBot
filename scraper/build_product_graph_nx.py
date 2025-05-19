import os
import json
import pickle
import networkx as nx

INPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/structured_product_data.json")
OUTPUT_GRAPH = os.path.join(os.path.dirname(__file__), "../data/product_graph.gpickle")
OUTPUT_GRAPHML = os.path.join(os.path.dirname(__file__), "../data/product_graph.graphml")

# Define commonly shared, low-value ingredients
COMMON_INGREDIENTS = {
    "sugar", "salt", "water", "milk", "glucose", "cocoa", "soy lecithin",
    "natural flavour", "vanillin", "lactose", "modified milk ingredients"
}

def normalize(ingredient):
    return ingredient.lower().strip()

def build_graph():
    with open(INPUT_FILE) as f:
        data = json.load(f)

    G = nx.DiGraph()

    for entry in data:
        pname = entry["name"]
        brand = entry["brand"]
        category = entry["category"]
        ingredients = entry.get("ingredients", "")

        G.add_node(pname, type="Product")
        G.add_node(brand, type="Brand")
        G.add_node(category, type="Category")

        G.add_edge(pname, brand, type="BELONGS_TO")
        G.add_edge(pname, category, type="IN_CATEGORY")

        for ing in [i.strip() for i in ingredients.split(",") if i.strip()]:
            ing_norm = normalize(ing)
            if ing_norm in COMMON_INGREDIENTS:
                continue  # Skip generic ingredient

            G.add_node(ing, type="Ingredient")
            G.add_edge(pname, ing, type="CONTAINS")

    # Save graph
    with open(OUTPUT_GRAPH, "wb") as f:
        pickle.dump(G, f)

    nx.write_graphml(G, OUTPUT_GRAPHML)

    print(f"✅ Graph built with {len(G.nodes)} nodes and {len(G.edges)} edges.")
    print(f"📦 Saved to:\n - {OUTPUT_GRAPH}\n - {OUTPUT_GRAPHML}")

if __name__ == "__main__":
    build_graph()
