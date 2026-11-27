from datetime import datetime, timedelta

# cada consulta va directo a una sola particion porque el where usa la partition key completa
# por eso ninguna necesita allow filtering

QUERIES = {
    # req 1
    "last_sessions": """
        SELECT user_id, session_start, game_id, game_title, platform, duration_minutes
        FROM sessions_by_user
        WHERE user_id = ?
        LIMIT 20""",
    # req 2
    "sessions_in_range": """
        SELECT user_id, session_start, session_end, game_id, game_title, duration_minutes
        FROM sessions_by_user
        WHERE user_id = ? AND session_start >= ? AND session_start < ?""",
    # req 3
    "sessions_by_game": """
        SELECT user_id, game_id, session_start, duration_minutes, achievements_unlocked
        FROM sessions_by_user_game
        WHERE user_id = ? AND game_id = ?""",
    # req 4
    "playtime_by_day": """
        SELECT user_id, play_date, total_minutes, sessions_count
        FROM playtime_by_user_day
        WHERE user_id = ? AND month = ?""",
    # req 5
    "game_sessions_on_date": """
        SELECT game_id, play_date, session_start, user_id, duration_minutes
        FROM sessions_by_game_day
        WHERE game_id = ? AND play_date = ?
        LIMIT 100""",
    # req 6
    "last_achievements": """
        SELECT user_id, unlocked_at, game_id, game_title, achievement_name
        FROM achievements_by_user
        WHERE user_id = ?
        LIMIT 30""",
    # req 7
    "sessions_by_platform": """
        SELECT user_id, platform, session_start, game_title, duration_minutes
        FROM sessions_by_user_platform
        WHERE user_id = ? AND platform = ?
        LIMIT 25""",
    # req 8
    "activity_by_hour": """
        SELECT game_id, play_date, hour, sessions_started, total_minutes
        FROM activity_by_game_hour
        WHERE game_id = ? AND play_date = ?""",
}

# los prepared statements se preparan una sola vez y se reutilizan
_prepared = {}


def run(session, name, params):
    if name not in _prepared:
        _prepared[name] = session.prepare(QUERIES[name])
    return list(session.execute(_prepared[name], params))


def to_date(text):
    # convierte "2026-10-15" a fecha
    return datetime.strptime(text, "%Y-%m-%d").date()


# ---------------------------------------------------------------
# una funcion por requerimiento
# ---------------------------------------------------------------
def last_sessions(session, user_id):
    return run(session, "last_sessions", (user_id,))


def sessions_in_range(session, user_id, start_text, end_text):
    # el dia final se incluye completo, por eso se le suma un dia y se usa <
    start = datetime.strptime(start_text, "%Y-%m-%d")
    end = datetime.strptime(end_text, "%Y-%m-%d") + timedelta(days=1)
    return run(session, "sessions_in_range", (user_id, start, end))


def sessions_by_game(session, user_id, game_id):
    return run(session, "sessions_by_game", (user_id, game_id))


def playtime_by_day(session, user_id, month):
    return run(session, "playtime_by_day", (user_id, month))


def game_sessions_on_date(session, game_id, date_text):
    return run(session, "game_sessions_on_date", (game_id, to_date(date_text)))


def last_achievements(session, user_id):
    return run(session, "last_achievements", (user_id,))


def sessions_by_platform(session, user_id, platform):
    return run(session, "sessions_by_platform", (user_id, platform))


def activity_by_hour(session, game_id, date_text):
    return run(session, "activity_by_hour", (game_id, to_date(date_text)))


# ---------------------------------------------------------------
# ayudas para el menu
# ---------------------------------------------------------------
def sample_values(session):
    # trae una sesion cualquiera para sugerir valores que si existen
    row = session.execute(
        "SELECT user_id, session_start, game_id, platform FROM sessions_by_user LIMIT 1"
    ).one()
    if row is None:
        return None
    return {
        "user_id": row.user_id,
        "game_id": row.game_id,
        "platform": row.platform,
        "date": row.session_start.strftime("%Y-%m-%d"),
        "month": row.session_start.strftime("%Y-%m"),
    }
