import os

# ruta del archivo con las tablas
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.cql")

TABLES = [
    "sessions_by_user",
    "sessions_by_user_game",
    "playtime_by_user_day",
    "sessions_by_game_day",
    "achievements_by_user",
    "sessions_by_user_platform",
    "activity_by_game_hour",
]


def create_schema(session):
    # lee schema.cql y ejecuta cada sentencia separada por ;
    with open(SCHEMA_FILE, encoding="utf-8") as f:
        text = f.read()

    # se quitan los comentarios para que no estorben
    lines = [line for line in text.splitlines() if not line.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

    for statement in statements:
        session.execute(statement)
    print("tablas de cassandra creadas")


def truncate_tables(session):
    # borra los datos anteriores para que no se mezclen al volver a cargar
    for table in TABLES:
        session.execute(f"TRUNCATE {table}")
