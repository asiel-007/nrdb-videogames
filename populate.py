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