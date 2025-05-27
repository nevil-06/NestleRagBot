from gremlin_python.driver import client, serializer

def create_gremlin_client(endpoint, key, database, graph):
    return client.Client(
        f"{endpoint}/gremlin",
        "g",
        username=f"/dbs/{database}/colls/{graph}",
        password=key,
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

def add_vertex(g_client, label, id, name, partition_key):
    query = f"g.addV('{label}')" \
            f".property('id', '{id}')" \
            f".property('name', '{name}')" \
            f".property('partitionKey', '{partition_key}')"
    return g_client.submit(query).all().result()

def add_edge(g_client, from_id, to_id, edge_label):
    query = f"g.V('{from_id}').addE('{edge_label}').to(g.V('{to_id}'))"
    return g_client.submit(query).all().result()
