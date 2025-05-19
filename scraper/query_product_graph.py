import pickle
import networkx as nx

GRAPH_FILE = "data/product_graph.gpickle"

def load_graph():
    with open(GRAPH_FILE, "rb") as f:
        return pickle.load(f)

def products_by_ingredient(G, ingredient):
    return [n for n in G.predecessors(ingredient) if G.nodes[n]["type"] == "Product"]

def ingredients_by_product(G, product):
    return [n for n in G.successors(product) if G.nodes[n]["type"] == "Ingredient"]

def similar_products(G, product):
    ingredients = ingredients_by_product(G, product)
    related = set()
    for ing in ingredients:
        for p in G.predecessors(ing):
            if G.nodes[p]["type"] == "Product" and p != product:
                related.add(p)
    return sorted(related)

def main():
    G = load_graph()
    print("✅ Product Graph Loaded")
    print("Available queries:")
    print("1. Find all products that contain an ingredient")
    print("2. Find all ingredients in a product")
    print("3. Find products with shared ingredients")
    print("4. Exit")

    while True:
        choice = input("\nEnter your choice (1/2/3/4): ").strip()
        if choice == "1":
            ing = input("Enter ingredient name: ").strip()
            if not G.has_node(ing):
                print("❌ Ingredient not found.")
                continue
            results = products_by_ingredient(G, ing)
            print(f"\n🧾 Products containing '{ing}':")
            for r in results:
                print(" -", r)
        elif choice == "2":
            prod = input("Enter product name: ").strip()
            if not G.has_node(prod):
                print("❌ Product not found.")
                continue
            results = ingredients_by_product(G, prod)
            print(f"\n🧾 Ingredients in '{prod}':")
            for r in results:
                print(" -", r)
        elif choice == "3":
            prod = input("Enter product name: ").strip()
            if not G.has_node(prod):
                print("❌ Product not found.")
                continue
            results = similar_products(G, prod)
            print(f"\n🧾 Products sharing ingredients with '{prod}':")
            for r in results:
                print(" -", r)
        elif choice == "4":
            break
        else:
            print("❌ Invalid input.")

if __name__ == "__main__":
    main()
