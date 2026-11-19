# DATOS COMPARTIDOS
"""
Antes de poblar cualquier base se corre un solo paso de generación de datos, para que las tres bases
usen exactamente los mismos juegos y usuarios con los mismos ids.

Se lee el archivo data/games.csv (dataset "Video Game Sales with Ratings" de Kaggle), que
contiene las columnas Name, Platform, Year_of_Release, Genre, Publisher, ventas, Critic_Score,
Critic_Count, User_Score, User_Count, Developer y Rating.

Se descartan las filas que no tienen Year_of_Release, Developer, Rating, Critic_Score o User_Score,
y las que tienen "tbd" en User_Score. Como el mismo juego aparece una vez por cada plataforma, se
agrupan las filas por Name para que cada juego quede una sola vez con su lista de plataformas. Si
Developer trae varios estudios separados por coma, se toma solo el primero.

De los juegos limpios se eligen alrededor de 400 al azar y a cada uno se le asigna un game_id
(g_0001, g_0002, ...). Su average_rating se calcula con las calificaciones reales del dataset,
convirtiendo Critic_Score (0 a 100) y User_Score (0 a 10) a una escala de 1 a 5 y promediándolos.

Con Faker se generan unos 200 usuarios con user_id (u_0001, u_0002, ...) y name. A cada usuario se
le asignan 2 o 3 géneros favoritos y entre 10 y 30 juegos jugados, la mayoría de esos géneros, para
que las recomendaciones tengan sentido. Por cada juego jugado se genera una calificación del 1 al 5
cercana al average_rating del juego, y se marca como favorito si la calificación es 5. También se
genera a quién sigue cada usuario (entre 5 y 20 personas) y las relaciones de similitud entre
juegos, tomando para cada juego de 2 a 4 juegos del mismo género. El total_players de cada juego se
calcula contando cuántos usuarios lo jugaron.

Todo esto se guarda en data/ como games.json, users.json, follows.json y played.json. Las tres
secciones de abajo leen estos archivos.
"""

# CASSANDRA
"""
Las sesiones no vienen en ningún dataset, así que se generan con Python a partir de data/played.json.
Así, si un usuario jugó un juego en Dgraph, también tiene sesiones de ese juego en Cassandra.

Por cada par usuario y juego se generan entre 3 y 15 sesiones con fechas entre enero y octubre de
2026. Cada sesión tiene session_start, una duración de 15 a 240 minutos (con la que se calcula
session_end), una plataforma tomada de las plataformas del juego y achievements_unlocked entre 0 y 3.
Por cada logro desbloqueado se genera un registro con achievement_id, achievement_name (creado con
Faker) y unlocked_at dentro del tiempo de esa sesión.

Primero se crea el keyspace game_activity con sus siete tablas. Luego cada sesión se inserta en las
cuatro tablas de sesiones, que son sessions_by_user, sessions_by_user_game, sessions_by_game_day y
sessions_by_user_platform, y cada logro se inserta en achievements_by_user.

Los totales se calculan en el script antes de insertar, porque en Cassandra no conviene sumar al
momento de consultar. Para playtime_by_user_day se agrupan las sesiones por usuario y día, se suman
los minutos y se cuentan las sesiones, y se guarda una fila por día con su month correspondiente.
Para activity_by_game_hour se agrupan las sesiones por juego, día y hora de inicio, y se guarda una
fila por hora con sessions_started y total_minutes.
"""

# MONGODB
"""
La colección games se llena con data/games.json. Cada juego se inserta como un documento usando
los datos del dataset de la siguiente forma:

game {
    game_id: id generado
    title: Name
    developer: Developer
    publisher: Publisher
    release_date: Year_of_Release con mes y día aleatorios
    genres: [Genre]
    age_rating: Rating
    average_rating: calculado con Critic_Score y User_Score
    platforms: [{ name: Platform, price: precio aleatorio }] por cada plataforma del juego
}

Los campos que no trae el dataset se generan. description se crea con Faker, languages se elige al
azar de una lista (es, en, fr, de, ja, ...), game_modes se elige al azar entre single_player,
local_multiplayer y online_multiplayer, y cover_url se arma con una url de ejemplo usando el
game_id. Solo los juegos que salen para PC llevan system_requirements con requisitos mínimos y
recomendados generados al azar.

genres se guarda como arreglo aunque el dataset traiga un solo género, porque en la realidad un
juego puede tener varios. A algunos juegos se les puede agregar un género secundario al azar.

Después de insertar se crean los índices de la colección.
"""

# DGRAPH
"""
Primero se carga el esquema con los tipos User, Game, Developer y Genre, sus índices y las
relaciones marcadas con @reverse, para poder recorrerlas en ambos sentidos.

Los datos salen de los archivos de data/ y se usan de la siguiente forma:

Game {
    game_id: id generado
    title: Name
    release_year: Year_of_Release
    average_rating: calculado con Critic_Score y User_Score
    total_players: número de usuarios que lo jugaron
}

Genre {
    genre_name: Genre
}

Developer {
    developer_name: Developer
}

User {
    user_id: id generado
    name: generado con Faker
}

Primero se insertan los nodos Genre y Developer sin repetir, sacando los valores únicos de todos los
juegos, y se guarda el uid que Dgraph le asigna a cada uno. Luego se insertan los juegos y, al mismo
tiempo, sus relaciones BELONGS_TO_GENRE y DEVELOPED_BY usando esos uids. Así no hay que revisar en
cada juego si el género o el desarrollador ya existían.

Después se insertan los usuarios y sus relaciones. FOLLOWS sale de follows.json. HAS_PLAYED sale de
played.json con los facets favorite y rating. SIMILAR_TO se crea en ambos sentidos, porque si un
juego es parecido a otro, el otro también es parecido al primero.

Platform ya no se guarda en Dgraph porque ninguna consulta del grafo la usa y esa información ya
vive en MongoDB.
"""


from connect import connect_cassandra, connect_mongo, connect_dgraph
import dgraph.dgraph_schema as dgraph_schema
from pydgraph import DgraphClient
from pydgraph.errors import ConnectionError, TransactionError
from faker import Faker
import pandas as pd
import os
import json
import random

SRC_CSV = "./data/games.csv"
JSON_GAMES = "./data/games.json"
JSON_USERS = "./data/users.json"
JSON_FOLLOWS = "./data/follows.json"
JSON_PLAYED = "./data/played.json"
COLS = ["Name", "Year_of_Release", "Developer", "Rating",
        "Critic_Score", "User_Score", "User_Count"]


def get_sample(n_games=400) -> pd.DataFrame:
    if os.path.exists(JSON_GAMES):
        df = pd.read_json(JSON_GAMES, orient="records")
        df["platforms"] = df["platforms"].apply(
            lambda s: [p for p in s.split("|") if p]
        )
        return df
    df = pd.read_csv(SRC_CSV)
    # Reemplazar los valores nulos escritos para que sean eliminados
    for c in COLS:
        df[c] = df[c].astype(str).str.strip().replace({"N/A": pd.NA})
    df = df.dropna()
    # Eliminar "tbd" del score
    drop_tbd = df[df["User_Score"] == "tbd"].index
    df = df.drop(drop_tbd)
    # Tomar el primer Developer si aparecen varios
    df["Developer"] = df["Developer"].astype(str).str.split(",").str[0].str.strip()
    # Reconvertir columnas numéricas
    df["User_Score"] = pd.to_numeric(df["User_Score"])
    df["Critic_Score"] = pd.to_numeric(df["Critic_Score"])
    df["Year_of_Release"] = pd.to_numeric(df["Year_of_Release"])
    df["Year_of_Release"] = df["Year_of_Release"].astype(int)
    df["User_Count"] = pd.to_numeric(df["User_Count"])
    df["User_Count"] = df["User_Count"].astype(int)
    # Calcular el promedio de score de los críticos (1-100) y usuarios (1-10)
    # y regularDiagramaizarlo al rango 1-5
    critic_1_5 = df["Critic_Score"] / 20.0
    user_1_5 = df["User_Score"] / 2.0
    df["average_rating"] = ((critic_1_5 + user_1_5) / 2.0)
    # Agrupar por título para obtener todas las plataformas y
    # el primer developer
    agg = df.groupby(["Name"], as_index=False).agg(
            platforms=("Platform", lambda s: "|".join(sorted(set(s.astype(str))))),
            release_year=("Year_of_Release", "first"),
            genre=("Genre", "first"),
            publisher=("Publisher", "first"),
            developer=("Developer", "first"),
            age_rating=("Rating", "first"),
            total_players=("User_Count", "first"),
            average_rating=("average_rating", "mean")
        )
    agg["average_rating"] = agg["average_rating"].round(2)
    # Obtener muestra de n videojuegos
    n = min(n_games, len(agg))
    sample = agg.sample(n=n, random_state=42)
    # Generar los ids
    sample["game_id"] = [f"g_{i+1:04d}" for i in range(len(sample))]
    sample["game_id"] = [f"g_{i+1:04d}" for i in range(len(sample))]
    # Renombrar columnas para coincidir con los modelos de datos
    sample = sample.rename(columns={"Name": "title"})
    sample.to_json(JSON_GAMES, index=False, indent=2, orient="records")
    return sample


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


def get_played(path: str, games: pd.DataFrame, users: pd.DataFrame) -> list:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    by_genre = {}
    for _, g in games.iterrows():
        by_genre.setdefault(g["genre"], []).append(g["game_id"])
    all_genres = list(by_genre.keys())
    rating_by_game = dict(zip(games["game_id"], games["average_rating"]))
    data = []
    for _, u in users.iterrows():
        n_total = random.randint(10, 30)
        # 2-3 favorite genres, 2-3 extra genres
        n_fav = random.randint(2, min(3, len(all_genres)))
        fav_genres = random.sample(all_genres, n_fav)
        other_genres = [g for g in all_genres if g not in fav_genres]
        n_other = random.randint(2, min(3, len(other_genres)))
        other_genres = random.sample(other_genres, n_other)
        # choose number of favorite games, leave at least 1 non-favorite
        n_fav = random.randint(1, n_total - 1)
        n_other = n_total - n_fav
        pool_fav = list({gid for g in fav_genres for gid in by_genre[g]})
        pool_other = list({gid for g in other_genres for gid in by_genre[g]})

        fav_games = random.sample(pool_fav, min(n_fav, len(pool_fav)))
        # if pool is not big enough, take extra games
        other_games = random.sample(pool_other, min(n_other, len(pool_other)))
        if len(fav_games) + len(other_games) < n_total:
            used = set(fav_games) | set(other_games)
            rest = [g for g in games["game_id"] if g not in used]
            extra = random.sample(rest, n_total - len(fav_games) - len(other_games))
            other_games += extra
        # build objects
        for gid in fav_games:
            avg = rating_by_game[gid]
            rating = max(1, min(5, int(round(random.gauss(avg, 0.7)))))
            data.append({"user_id": u["user_id"], "g_id": gid,
                         "rating": rating, "favorite": True})
        for gid in other_games:
            avg = rating_by_game[gid]
            rating = max(1, min(5, int(round(random.gauss(avg, 0.7)))))
            data.append({"user_id": u["user_id"], "g_id": gid,
                         "rating": rating, "favorite": False})
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return data


def populate_dgraph(client: DgraphClient, data: pd.DataFrame) -> None:
    # inserting nodes
    games_cols = ["game_id", "title", "release_year",
                  "average_rating", "total_players"]
    games = dgraph_schema.parse_df(df=data, entity="Game", cols=games_cols)
    games_uids = dgraph_schema.insert_data(client=client, data=games,
                                           id_key="game_id")
    genres_values = data["genre"].unique().tolist()
    genres = [{"uid": f"_:ge_{i}",
               "genre_name": g,
               "genre_id": f"ge_{i}"}
              for i, g in enumerate(genres_values, start=1)]
    genres_uids = dgraph_schema.insert_data(client=client, data=genres,
                                            id_key="genre_name")
    developer_values = data["developer"].unique().tolist()
    developers = [{"uid": f"_:d_{i}",
                   "dev_name": d,
                   "dev_id": f"d_{i}"}
                  for i, d in enumerate(developer_values, start=1)]
    developers_uids = dgraph_schema.insert_data(client=client, data=developers,
                                                id_key="dev_name")
    users_df = get_users(JSON_USERS, 200)
    users_cols = ["user_id", "username"]
    users = dgraph_schema.parse_df(df=users_df, entity="User", cols=users_cols)
    users_uids = dgraph_schema.insert_data(client=client, data=users,
                                           id_key="user_id")
    # inserting edges
    follows = get_follows(JSON_FOLLOWS, users_uids)
    follows_edges = [{
        "follower": users_uids[f["follower"]],
        "follows": users_uids[f["follows"]]
    } for f in follows]
    dgraph_schema.insert_edges(client=client, edges=follows_edges,
                               from_key="follower", to_key="follows", pred="follows")
    # map every game to its developer and genre
    genre_id = {g: uid for g, uid in genres_uids.items()}
    dev_id = {d: uid for d, uid in developers_uids.items()}
    genre_edges = []
    dev_edges = []
    for _, row in data.iterrows():
        g_uid = games_uids[row["game_id"]]
        ge_uid = genre_id[row["genre"]]
        d_uid = dev_id[row["developer"]]
        genre_edges.append({"g_id": g_uid, "ge_id": ge_uid})
        dev_edges.append({"g_id": g_uid, "d_id": d_uid})
    dgraph_schema.insert_edges(client=client, edges=dev_edges,
                               from_key="g_id", to_key="d_id", pred="developed_by")
    dgraph_schema.insert_edges(client=client, edges=genre_edges,
                               from_key="g_id", to_key="ge_id", pred="belongs_to_genre")
    played = get_played(JSON_PLAYED, games=data, users=users_df)
    played_edges = [{
        "user_id": users_uids[p["user_id"]],
        "g_id": games_uids[p["g_id"]],
        "rating": int(p["rating"]),
        "favorite": bool(p["favorite"]),
    } for p in played]
    dgraph_schema.insert_edges(client=client, edges=played_edges,
                               from_key="user_id", to_key="g_id",
                               facets=["favorite", "rating"], pred="played")


def main():
    try:
        dgraph_client = connect_dgraph()
        dgraph_schema.create_schema(client=dgraph_client)
        data = get_sample()
        populate_dgraph(dgraph_client, data)
    except ConnectionError as e:
        print(f"Error al conectar Dgraph: {e}")
    except TransactionError as e:
        print(f"Error al cargar datos de Dgraph: {e}")


if __name__ == "__main__":
    main()
