import csv

from pandas import DataFrame
from pydgraph import DgraphClient, Operation


def create_schema(client: DgraphClient) -> None:
    """
    Creación de schema definido
    """
    schema = """
    user_id: string @index(exact) .
    username: string @index(hash) .
    game_id: string @index(exact) .
    title: string .
    release_year: int .
    average_rating: float .
    total_players: int @index(int) .
    genre_id: string .
    genre_name: string .
    dev_id: string .
    dev_name: string .
    played: [uid] @reverse .
    favorite: bool .
    rating: float .
    follows: [uid] @reverse .
    belongs_to_genre: [uid] @reverse .
    developed_by: [uid] @reverse .
    similar_to: [uid] @reverse .
    type User {
        user_id
        username
        played
        follows
    }
    type Game {
        game_id
        title
        release_year
        average_rating
        total_players
        belongs_to_genre
        developed_by
        similar_to
    }
    type Genre {
        genre_id
        genre_name
    }
    type Developer {
        dev_id
        dev_name
    }
    """
    try:
        client.alter(Operation(schema=schema))
    except Exception as e:
        print(f"Error al crear schema de Dgraph: {e}")


def parse_df(df: DataFrame, entity: str, cols: list) -> list:
    data = []
    subset = df[cols]
    for i, row in enumerate(subset.itertuples(name=entity), start=0):
        item = row._asdict()
        item["uid"] = f"_:{entity.lower()}_{i}"
        data.append(item)
    return data


def insert_data(client: DgraphClient, data: list, id_key: str) -> dict:
    txn = client.txn()
    res = txn.mutate(set_obj=data)
    txn.commit()
    uids = {}
    for item in data:
        id = item[id_key]
        label = item["uid"]
        uids[id] = res.uids[label.split(":")[1]]
    return uids


def drop_schema(client: DgraphClient):
    client.alter(Operation(drop_all=True))
