-- modelo de datos de cassandra (keyspace game_activity)
-- cada tabla esta pensada para responder una consulta especifica del menu

CREATE KEYSPACE IF NOT EXISTS game_activity
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE game_activity;

-- req 1 y 2: ultimas sesiones de un usuario y sesiones en un rango de fechas
CREATE TABLE IF NOT EXISTS sessions_by_user (
    user_id text,
    session_start timestamp,
    session_end timestamp,
    game_id text,
    game_title text,
    platform text,
    duration_minutes int,
    PRIMARY KEY ((user_id), session_start)
) WITH CLUSTERING ORDER BY (session_start DESC);

-- req 3: historial de un usuario con un juego especifico
CREATE TABLE IF NOT EXISTS sessions_by_user_game (
    user_id text,
    game_id text,
    session_start timestamp,
    duration_minutes int,
    achievements_unlocked int,
    PRIMARY KEY ((user_id, game_id), session_start)
) WITH CLUSTERING ORDER BY (session_start DESC);

-- req 4: minutos jugados por dia en un mes (valores precalculados)
CREATE TABLE IF NOT EXISTS playtime_by_user_day (
    user_id text,
    month text,
    play_date date,
    total_minutes int,
    sessions_count int,
    PRIMARY KEY ((user_id, month), play_date)
) WITH CLUSTERING ORDER BY (play_date ASC);

-- req 5: sesiones de un juego en una fecha
-- user_id va en la clustering key para que dos sesiones del mismo segundo no se pisen
CREATE TABLE IF NOT EXISTS sessions_by_game_day (
    game_id text,
    play_date date,
    session_start timestamp,
    user_id text,
    duration_minutes int,
    PRIMARY KEY ((game_id, play_date), session_start, user_id)
) WITH CLUSTERING ORDER BY (session_start DESC, user_id ASC);

-- req 6: ultimos logros de un usuario
CREATE TABLE IF NOT EXISTS achievements_by_user (
    user_id text,
    unlocked_at timestamp,
    achievement_id text,
    game_id text,
    game_title text,
    achievement_name text,
    PRIMARY KEY ((user_id), unlocked_at, achievement_id)
) WITH CLUSTERING ORDER BY (unlocked_at DESC, achievement_id ASC);

-- req 7: sesiones de un usuario en una plataforma
CREATE TABLE IF NOT EXISTS sessions_by_user_platform (
    user_id text,
    platform text,
    session_start timestamp,
    game_title text,
    duration_minutes int,
    PRIMARY KEY ((user_id, platform), session_start)
) WITH CLUSTERING ORDER BY (session_start DESC);

-- req 8: actividad por hora de un juego en un dia (valores precalculados)
CREATE TABLE IF NOT EXISTS activity_by_game_hour (
    game_id text,
    play_date date,
    hour int,
    sessions_started int,
    total_minutes int,
    PRIMARY KEY ((game_id, play_date), hour)
) WITH CLUSTERING ORDER BY (hour ASC);
