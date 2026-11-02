import os

import pydgraph
from pymongo import MongoClient
from cassandra.cluster import Cluster


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


CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "game_activity")


def connect_cassandra():
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect()
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    session.set_keyspace(CASSANDRA_KEYSPACE)
    return session