import pickle
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
with open("data/product_graph.gpickle", "rb") as f:
    G = pickle.load(f)

# Filter to only show Product → Ingredient edges (optional)
edges = [(u, v) for u, v, d in G.edges(data=True) if d["type"] == "CONTAINS"]
subG = G.edge_subgraph(edges).copy()

# Layout and draw
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(subG, k=0.4)
nx.draw(subG, pos, with_labels=True, node_size=200, font_size=8, arrows=False)
plt.title("Product–Ingredient Graph")
plt.show()
