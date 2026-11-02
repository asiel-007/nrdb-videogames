import pydgraph

client_stub = pydgraph.DgraphClientStub('localhost:9080')
dgraph_client = pydgraph.DgraphClient(client_stub)

print(dgraph_client.check_version())
