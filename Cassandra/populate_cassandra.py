import json
import os
import random
from collections import defaultdict
from datetime import datetime, timedelta

from cassandra.concurrent import execute_concurrent_with_args
from faker import Faker

from Cassandra.schema import create_schema, truncate_tables

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# misma semilla para que los datos salgan igual cada vez que se carga
random.seed(7)
fake = Faker()
Faker.seed(7)

# las sesiones se generan entre enero y octubre de 2026
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 10, 31, 23, 59)


# ---------------------------------------------------------------
# lectura de datos compartidos
# ---------------------------------------------------------------
def platform_names(game):
    # las plataformas pueden venir como texto o como {name, price}
    names = []
    for p in game.get("platforms", []):
        names.append(p["name"] if isinstance(p, dict) else p)
    return names or ["PC"]


def load_shared_data():
    # usa los archivos que crea generate_data.py, asi coincide con mongodb y dgraph
    with open(os.path.join(DATA_DIR, "games.json"), encoding="utf-8") as f:
        games = json.load(f)
    with open(os.path.join(DATA_DIR, "played.json"), encoding="utf-8") as f:
        played = json.load(f)
    print(f"usando {len(games)} juegos y {len(played)} relaciones de data/played.json")
    return games, played


# ---------------------------------------------------------------
# generacion de sesiones y logros
# ---------------------------------------------------------------
def random_datetime():
    # fecha y hora al azar dentro del rango, sin segundos para que se lea mejor
    total = int((END_DATE - START_DATE).total_seconds() // 60)
    return START_DATE + timedelta(minutes=random.randint(0, total))


def generate_sessions(games, played):
    games_by_id = {g["game_id"]: g for g in games}
    sessions = []
    achievements = []
    used_starts = defaultdict(set)  # para que un usuario no empiece dos sesiones al mismo minuto

    for rel in played:
        game = games_by_id.get(rel["game_id"])
        if game is None:
            continue
        user_id = rel["user_id"]
        platforms = platform_names(game)
        achievement_count = 0

        for _ in range(random.randint(3, 15)):
            start = random_datetime()
            while start in used_starts[user_id]:
                start += timedelta(minutes=1)
            used_starts[user_id].add(start)

            duration = random.randint(15, 240)
            unlocked = random.choices([0, 1, 2, 3], weights=[50, 30, 15, 5])[0]

            sessions.append({
                "user_id": user_id,
                "game_id": game["game_id"],
                "game_title": game["title"],
                "platform": random.choice(platforms),
                "session_start": start,
                "session_end": start + timedelta(minutes=duration),
                "duration_minutes": duration,
                "achievements_unlocked": unlocked,
            })

            # cada logro se desbloquea en algun momento de la sesion
            for _ in range(unlocked):
                achievement_count += 1
                achievements.append({
                    "user_id": user_id,
                    "unlocked_at": start + timedelta(minutes=random.randint(1, duration)),
                    "achievement_id": f"{game['game_id']}_a{achievement_count:03d}",
                    "game_id": game["game_id"],
                    "game_title": game["title"],
                    "achievement_name": fake.catch_phrase(),
                })

    return sessions, achievements


# ---------------------------------------------------------------
# totales precalculados (cassandra no suma al consultar)
# ---------------------------------------------------------------
def playtime_per_day(sessions):
    # agrupa por usuario y dia de inicio, suma minutos y cuenta sesiones
    totals = defaultdict(lambda: [0, 0])
    for s in sessions:
        key = (s["user_id"], s["session_start"].date())
        totals[key][0] += s["duration_minutes"]
        totals[key][1] += 1

    rows = []
    for (user_id, day), (minutes, count) in totals.items():
        rows.append((user_id, day.strftime("%Y-%m"), day, minutes, count))
    return rows


def activity_per_hour(sessions):
    # agrupa por juego, dia y hora de inicio
    totals = defaultdict(lambda: [0, 0])
    for s in sessions:
        key = (s["game_id"], s["session_start"].date(), s["session_start"].hour)
        totals[key][0] += 1
        totals[key][1] += s["duration_minutes"]

    rows = []
    for (game_id, day, hour), (count, minutes) in totals.items():
        rows.append((game_id, day, hour, count, minutes))
    return rows


# ---------------------------------------------------------------
# insercion
# ---------------------------------------------------------------
def insert_rows(session, cql, rows, label):
    # prepared statement + inserciones en paralelo, mucho mas rapido que una por una
    statement = session.prepare(cql)
    execute_concurrent_with_args(session, statement, rows, concurrency=100, raise_on_first_error=True)
    print(f"  {label}: {len(rows)} filas")


def populate_cassandra(session):
    create_schema(session)
    truncate_tables(session)

    games, played = load_shared_data()
    sessions, achievements = generate_sessions(games, played)
    print(f"se generaron {len(sessions)} sesiones y {len(achievements)} logros")

    # desnormalizacion: cada sesion se escribe en las 4 tablas de sesiones
    insert_rows(session,
        "INSERT INTO sessions_by_user (user_id, session_start, session_end, game_id, game_title, platform, duration_minutes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(s["user_id"], s["session_start"], s["session_end"], s["game_id"], s["game_title"], s["platform"], s["duration_minutes"]) for s in sessions],
        "sessions_by_user")

    insert_rows(session,
        "INSERT INTO sessions_by_user_game (user_id, game_id, session_start, duration_minutes, achievements_unlocked) VALUES (?, ?, ?, ?, ?)",
        [(s["user_id"], s["game_id"], s["session_start"], s["duration_minutes"], s["achievements_unlocked"]) for s in sessions],
        "sessions_by_user_game")

    insert_rows(session,
        "INSERT INTO sessions_by_game_day (game_id, play_date, session_start, user_id, duration_minutes) VALUES (?, ?, ?, ?, ?)",
        [(s["game_id"], s["session_start"].date(), s["session_start"], s["user_id"], s["duration_minutes"]) for s in sessions],
        "sessions_by_game_day")

    insert_rows(session,
        "INSERT INTO sessions_by_user_platform (user_id, platform, session_start, game_title, duration_minutes) VALUES (?, ?, ?, ?, ?)",
        [(s["user_id"], s["platform"], s["session_start"], s["game_title"], s["duration_minutes"]) for s in sessions],
        "sessions_by_user_platform")

    insert_rows(session,
        "INSERT INTO achievements_by_user (user_id, unlocked_at, achievement_id, game_id, game_title, achievement_name) VALUES (?, ?, ?, ?, ?, ?)",
        [(a["user_id"], a["unlocked_at"], a["achievement_id"], a["game_id"], a["game_title"], a["achievement_name"]) for a in achievements],
        "achievements_by_user")

    insert_rows(session,
        "INSERT INTO playtime_by_user_day (user_id, month, play_date, total_minutes, sessions_count) VALUES (?, ?, ?, ?, ?)",
        playtime_per_day(sessions),
        "playtime_by_user_day")

    insert_rows(session,
        "INSERT INTO activity_by_game_hour (game_id, play_date, hour, sessions_started, total_minutes) VALUES (?, ?, ?, ?, ?)",
        activity_per_hour(sessions),
        "activity_by_game_hour")

    print("cassandra poblada")
