from dgraph.dgraph_schema import drop_schema
from connect import connect_dgraph


def main():
    client = connect_dgraph()
    drop_schema(client)


if __name__ == "__main__":
    main()
