from pydgraph import DgraphClient
import json


def query1(client: DgraphClient, user_id: str):
    """
    Juegos que le gustan a las personas que sigo
    Obtener los 3 juegos más populares que las personas
    que sigo marcaron como favoritos
    """
    query = """
    query followed_liked($u_id: string) {
      var(func: eq(user_id, $u_id)) {
        followed as follows { uid }
        my_played as played { uid }
      }
      # Encontrar los juegos que marcaron como favoritos y el usuario
      # no ha jugado
      result(func: uid(followed)) @filter(NOT uid(my_played)) {
        username
        played(orderdesc: total_players, first: 3) @facets(eq(favorite, true)) {
          game_id
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


def query2(client: DgraphClient, game_id: str):
    """
    Judeojuegosegos similares a uno dado
    Obtener los videojuegos que son similares a otro siguiendo
    las relaciones de similitud hasta dos niveles
    """
    query = """
    query similar_games($g_id: string) {
        # obtener uid del juego
        var(func: eq(game_id, $g_id)) {
            game as uid
        }
        # obtener vecinos directos
        var (func: uid(game)) {
            similar_to @filter (NOT uid(game)) { g1 as uid }
        }
        # obtener similares a los vecinos filtrando los directos
        # y el juego raíz
        result (func: uid(g1)) {
            game_id
            title
            similar_to @filter (NOT uid(g1, g2, game)) {
                g2 as uid
                game_id
                title
            }
        }
    }
    """
    try:
        res = client.txn(read_only=True).query(query=query,
                                               variables={"$g_id": game_id})
        json_res = json.loads(res.json)
        # Obtener valores únicos y asignar distancias
        similar = []
        seen = set()
        for n1 in json_res["result"]:
            if n1["game_id"] not in seen:
                seen.add(n1["game_id"])
                item = {
                    "game_id": n1["game_id"],
                    "title": n1["title"],
                    "distance": 1
                }
                similar.append(item)
        for n1 in json_res["result"]:
            for n2 in n1["similar_to"]:
                if n2["game_id"] not in seen:
                    seen.add(n2["game_id"])
                    item = {
                        "game_id": n2["game_id"],
                        "title": n2["title"],
                        "distance": 2
                    }
                    similar.append(item)
        return similar
    except Exception as e:
        print(f'Error al obtener "": {e}')


def query3(client: DgraphClient, user_id: str):
    """
    Identificar los 3 géneros más jugados por el usuario
    y recomendar hasta 15 videojuegos de estos géneros,
    ordenados por total_players
    """


def query4(client: DgraphClient):
    pass


def query5(client: DgraphClient):
    pass


def query6(client: DgraphClient):
    pass


def query7(client: DgraphClient, user_id: str):
    """
    Recomendar videojuegos de los desarrolladores
    de los videojuegos que el usuario calificó con 5 estrellas
    """
    query = """
    query liked_devs($u_id: string) {
        # Obtener juegos jugados por el usuario
        var (func: eq(user_id, $u_id)) {
            my_played as played { uid }
        }
        var (func: eq(user_id, $u_id)) {
            liked as played @facets(ge(rating, 4)) {
                uid
            }
        }
        var (func: uid(liked)) {
            dev as developed_by { uid }
        }
        result(func: uid(dev)) {
            dev_name
            games: ~developed_by @filter(NOT uid(my_played)){
                game_id
                title
                release_year
            }
        }
    }
    """
    try:
        res = client.txn(read_only=True).query(query=query,
                                               variables={"$u_id": user_id})
        # Eliminar los desarrolladores de los que no se encontraron juegos
        # sin jugar
        res_json = json.loads(res.json)
        devs = [dev for dev in res_json["result"] if "games" in dev]
        return devs
    except Exception as e:
        print(f'Error al obtener "": {e}')


def query8(client: DgraphClient):
    pass
