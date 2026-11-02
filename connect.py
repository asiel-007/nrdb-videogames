import pydgraph
import os

DGRAPH_ADDR = os.getenv("DGRAPH_ADDR", "localhost:9080")


def connect_dgraph():
    try:
        client_stub = pydgraph.DgraphClientStub('localhost:9080')
        dgraph_client = pydgraph.DgraphClient(client_stub)
        return dgraph_client
    except Exception as e:
        pass
