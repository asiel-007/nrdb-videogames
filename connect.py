import os

import pydgraph
from pymongo import MongoClient

DGRAPH_ADDR = os.getenv("DGRAPH_ADDR", "localhost:9080")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "game_catalog")


def connect_mongo():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    return client[MONGO_DB]


def connect_dgraph():
    try:
        client_stub = pydgraph.DgraphClientStub(DGRAPH_ADDR)
        dgraph_client = pydgraph.DgraphClient(client_stub)
        return dgraph_client
    except Exception as e:
        pass
