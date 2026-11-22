import pandas as pd
import os
import json
from faker import Faker
import random
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


def parse_df(df: pd.DataFrame, entity: str, cols: list) -> list:
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


def insert_edges(client: DgraphClient, edges: list, from_key: str, to_key: str, pred: str, facets=None) -> None:
    nqads = ""
    for e in edges:
        nqads += f"<{e[from_key]}> <{pred}> <{e[to_key]}> "
        if facets:
            nqads += "("
            for f in facets:
                nqads += f"{f}={str(e[f]).lower()},"
            nqads = nqads[:-1]
            nqads += ")"
        nqads += " .\n"
    print(nqads)
    txn = client.txn()
    try:
        txn.mutate(set_nquads=nqads)
        txn.commit()
    finally:
        txn.discard()
    # grouped = {}
    # for e in edges:
    #     grouped.setdefault(e[from_key], []).append(e)
    # edges_obj = []
    # for src, items in grouped.items():
    #     obj = {"uid": src, pred: []}
    #     for it in items:
    #         link = {"uid": it[to_key]}
    #         if facets:
    #             for f in facets:
    #                 link[f] = it[f]
    #         obj[pred].append(link)
    #     edges_obj.append(obj)
    # txn = client.txn()
    # try:
    #     txn.mutate(set_obj=edges_obj)
    #     txn.commit()
    # finally:
    #     txn.discard()


def get_users(path: str, n: int) -> pd.DataFrame:
    if os.path.exists(path):
        return pd.read_json(path, orient="records")
    fake = Faker()
    data = []
    for i in range(n):
        data.append({"user_id": f"u_{i+1:04d}", "username": fake.name()})
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return pd.read_json(path, orient="records")


def get_follows(path: str, user_ids: list) -> list:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    data = []
    for uid in user_ids:
        candidates = [u for u in user_ids if u != uid]
        n = random.randint(5, min(20, len(candidates)))
        for followed in random.sample(candidates, n):
            data.append({"follower": uid, "follows": followed})
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return data


def get_similar_to(path: str, games: pd.DataFrame) -> list:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    by_genre = {}
    for _, g in games.iterrows():
        by_genre.setdefault(g["genre"], []).append(g["game_id"])
    pairs = set()
    for _, ids in by_genre.items():
        if len(ids) < 2:
            continue
        for gid in ids:
            others = [x for x in ids if x != gid]
            # Muestra de 2-4 juegos del mismo género
            k = random.randint(2, min(4, len(others)))
            for other in random.sample(others, k):
                # construir cada par con los videojuegos seleccionados
                pairs.add(tuple(sorted((gid, other))))

    data = [{"g_id": a, "similar": b} for a, b in pairs]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return data


def drop_schema(client: DgraphClient):
    client.alter(Operation(drop_all=True))
