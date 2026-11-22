from pydgraph import DgraphClient
import json


def query1(client: DgraphClient, user_id: str):
    """
    Juegos que le gustan a las personas que sigo
    Obtener los juegos que al menos 2 de las personas
    que sigo marcaron como favoritos
    """
    query = """
    {
      var(func: eq(user_id, "u_0001")) {
        followed as follows {
          uid
        }
        my_played as played {
          uid
        }
      }
      # Encontrar los juegos que marcaron como favoritos y el usuario
      # no ha jugado
      result(func: uid(followed)) @filter(NOT uid(my_played)) {
        username
        played(orderdesc: total_players, first: 3) @facets(eq(favorite, true)) {
          title
          total_players
        }
      }
    }
    """
    try:
        res = client.txn(read_only=True).query(query=query,
                                               variables={'$u_id': user_id})
        return json.loads(res.json)
    except Exception as e:
        print(f'Error al obtener "Juegos que les gustan a las personas que sigo": {e}')
    pass


def query2(client: DgraphClient,):
    pass


def query3(client: DgraphClient):
    pass


def query4(client: DgraphClient):
    pass


def query5(client: DgraphClient):
    pass


def query6(client: DgraphClient):
    pass


def query7(client: DgraphClient):
    pass
