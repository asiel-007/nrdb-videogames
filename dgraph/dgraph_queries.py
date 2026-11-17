from pydgraph import DgraphClient
import json


def query1(client: DgraphClient, user_id: str):
    """
    Juegos que le gustan a las personas que sigo
    Obtener los juegos que al menos 2 de las personas
    que sigo marcaron como favoritos
    """
    query = """
    query followed_liked($uid: string) {
        # Encontrar usuarios seguidos y juegos jugados
        var(func: eq(user_id, $uid)) {
            follows {
                friend_uid as uid
            }
            played {
                played_uid as uid
            }
        }
        # Encontrar los juegos que marcaron como favoritos
        var(func: uid(friend_uid)) {
            played @facets(favorite) @filter(eq(favorite, true)){
                g as uid
            }
        }
        # Contar los usuarios que marcaron cada juego como
        # favorito
        var(func: uid(g)) @groupby(uid(g)) {
            c as count(uid)
        }
        # Regresar los juegos para los que se hayan contado
        # dos facets favorite y no haya sido jugados por el usuario
        result(func: uid(c), orderdesc: val(c), first: 10)
            @filter(ge(val(c), 2) AND NOT uid(played_uid)) {
            game_id
            title
            friends_who_liked: val(c)
        }
    }
    """
    try:
        res = client.txn(read_only=True).query(query=query,
                                               variables={'$user_id': user_id})
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
