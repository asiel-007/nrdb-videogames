"""
genera los datos compartidos para las tres bases.
lee data/games.csv y crea en data/:
    games.json    juegos limpios con su game_id
    users.json    usuarios con user_id
    follows.json  a quien sigue cada usuario
    played.json   que juegos jugo cada usuario, con rating y favorito
    similar.json  juegos parecidos entre si

se corre una sola vez antes de populate.py:
    python generate_data.py
"""

import csv
import json
import os
import random
from collections import Counter, defaultdict

from faker import Faker

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

NUM_GAMES = 400
NUM_USERS = 200
VALID_AGE_RATINGS = {"E", "E10+", "T", "M"}

# misma semilla para que todos en el equipo obtengan exactamente los mismos datos
random.seed(7)
fake = Faker()
Faker.seed(7)


# ---------------------------------------------------------------
# 1. limpiar y agrupar el csv
# ---------------------------------------------------------------
def to_scale_1_5(value, max_value):
    # convierte una calificacion de 0 a max_value a una escala de 1 a 5
    return 1 + (value / max_value) * 4


def load_games():
    grouped = {}
    with open(os.path.join(DATA_DIR, "games.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # se descartan las filas incompletas
            if row["Year_of_Release"] in ("", "N/A") or not row["Developer"]:
                continue
            if row["Rating"] not in VALID_AGE_RATINGS:
                continue
            if row["Critic_Score"] == "" or row["User_Score"] in ("", "tbd"):
                continue

            name = row["Name"]
            if name not in grouped:
                # si developer trae varios estudios se toma el primero
                grouped[name] = {
                    "title": name,
                    "developer": row["Developer"].split(",")[0].strip(),
                    "publisher": row["Publisher"],
                    "genre": row["Genre"],
                    "age_rating": row["Rating"],
                    "release_year": int(float(row["Year_of_Release"])),
                    "platforms": [],
                    "critic_scores": [],
                    "user_scores": [],
                }
            game = grouped[name]

            # el mismo juego aparece una vez por plataforma, se juntan en una lista
            if row["Platform"] not in game["platforms"]:
                game["platforms"].append(row["Platform"])
            game["critic_scores"].append(float(row["Critic_Score"]))
            game["user_scores"].append(float(row["User_Score"]))
            game["release_year"] = min(game["release_year"], int(float(row["Year_of_Release"])))

    # se eligen los juegos al azar y se les pone su id
    names = random.sample(sorted(grouped), NUM_GAMES)
    games = []
    for i, name in enumerate(names, start=1):
        g = grouped[name]
        critic = sum(g["critic_scores"]) / len(g["critic_scores"])
        user = sum(g["user_scores"]) / len(g["user_scores"])
        average = (to_scale_1_5(critic, 100) + to_scale_1_5(user, 10)) / 2

        games.append({
            "game_id": f"g_{i:04d}",
            "title": g["title"],
            "developer": g["developer"],
            "publisher": g["publisher"],
            "genres": [g["genre"]],
            "platforms": g["platforms"],
            "release_year": g["release_year"],
            "age_rating": g["age_rating"],
            "critic_score": round(critic, 1),
            "user_score": round(user, 1),
            "average_rating": round(average, 2),
            "total_players": 0,  # se llena despues de generar played
        })
    return games


# ---------------------------------------------------------------
# 2. usuarios
# ---------------------------------------------------------------
def make_users(genres):
    users = []
    used_usernames = set()
    for i in range(1, NUM_USERS + 1):
        username = fake.user_name()
        while username in used_usernames:
            username = fake.user_name() + str(random.randint(1, 99))
        used_usernames.add(username)

        users.append({
            "user_id": f"u_{i:04d}",
            "username": username,
            "name": fake.name(),
            # cada usuario tiene 2 o 3 generos favoritos para que las recomendaciones tengan sentido
            "favorite_genres": random.sample(genres, random.randint(2, 3)),
        })
    return users


# ---------------------------------------------------------------
# 3. juegos jugados, con rating y favorito
# ---------------------------------------------------------------
def make_played(users, games):
    games_by_genre = defaultdict(list)
    for g in games:
        games_by_genre[g["genres"][0]].append(g)

    played = []
    for u in users:
        total = random.randint(10, 30)
        # la mayoria de sus juegos son de sus generos favoritos y el resto de cualquiera
        favorites_pool = [g for genre in u["favorite_genres"] for g in games_by_genre[genre]]
        from_favorites = min(int(total * 0.75), len(favorites_pool))

        chosen = random.sample(favorites_pool, from_favorites)
        others = [g for g in games if g not in chosen]
        chosen += random.sample(others, total - from_favorites)

        for g in chosen:
            # el rating del usuario queda cerca de la calificacion real del juego
            rating = round(g["average_rating"] + random.gauss(0, 0.8))
            rating = max(1, min(5, rating))
            played.append({
                "user_id": u["user_id"],
                "game_id": g["game_id"],
                "rating": rating,
                "favorite": rating == 5,
            })
    return played


# ---------------------------------------------------------------
# 4. a quien sigue cada usuario
# ---------------------------------------------------------------
def make_follows(users):
    ids = [u["user_id"] for u in users]
    follows = []
    for user_id in ids:
        others = [x for x in ids if x != user_id]
        for followed in random.sample(others, random.randint(5, 20)):
            follows.append({"follower": user_id, "followed": followed})
    return follows


# ---------------------------------------------------------------
# 5. juegos similares (por contenido, no por usuarios)
# ---------------------------------------------------------------
def similarity_score(a, b):
    # el genero es obligatorio, lo demas suma puntos
    score = 0
    if a["developer"] == b["developer"]:
        score += 2
    if set(a["platforms"]) & set(b["platforms"]):
        score += 1
    if abs(a["release_year"] - b["release_year"]) <= 3:
        score += 1
    if abs(a["average_rating"] - b["average_rating"]) <= 0.5:
        score += 1
    return score


def make_similar(games):
    similar = []
    seen = set()
    for a in games:
        candidates = [b for b in games if b["game_id"] != a["game_id"] and b["genres"][0] == a["genres"][0]]
        # se ordena por puntaje y se toman los 3 mejores
        candidates.sort(key=lambda b: (-similarity_score(a, b), b["game_id"]))
        for b in candidates[:3]:
            # se guarda en un solo sentido, en dgraph el @reverse da el otro
            pair = tuple(sorted((a["game_id"], b["game_id"])))
            if pair not in seen:
                seen.add(pair)
                similar.append({"game_id": a["game_id"], "similar_id": b["game_id"]})
    return similar


# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------
def save(name, data):
    with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  data/{name}: {len(data)} registros")


def generate_data():
    games = load_games()
    genres = sorted({g["genres"][0] for g in games})
    users = make_users(genres)
    played = make_played(users, games)
    follows = make_follows(users)
    similar = make_similar(games)

    # total_players se calcula contando cuantos usuarios jugaron cada juego
    counts = Counter(p["game_id"] for p in played)
    for g in games:
        g["total_players"] = counts[g["game_id"]]

    print("datos generados:")
    save("games.json", games)
    save("users.json", users)
    save("follows.json", follows)
    save("played.json", played)
    save("similar.json", similar)


if __name__ == "__main__":
    generate_data()
