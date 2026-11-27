# Recomendación de videojuegos
Integrantes del equipo:
- Axel Vázquez - 759603
- Daniel Jiménez - 756045
- Haziel Murillo - 757186

La idea es una plataforma web donde los jugadores pueden explorar un catálogo de videojuegos, ver la ficha de cada juego, revisar su propio historial de juego y recibir recomendaciones de qué jugar después. Dentro de la app el usuario podrá buscar juegos por nombre, género o plataforma, ver algunas estadísticas del catálogo (por ejemplo, qué géneros tienen mejor calificación o cuánto cuestan los juegos en cada consola), consultar cuánto y cuándo ha jugado, y ver qué juegan las personas que sigue.  
MongoDB guarda el catálogo, es decir juegos, géneros, plataformas, precios, idiomas, requisitos y demás metadatos. Cada juego trae información un poco distinta (uno de PC tiene requisitos de sistema, uno de consola no), así que los documentos flexibles nos acomodan muy bien. Dgraph guarda las conexiones, quién sigue a quién, quién jugó o marcó como favorito qué juego, a qué géneros pertenece cada juego, quién lo desarrolló y qué juegos se parecen entre sí, y de estas relaciones salen las recomendaciones. Cassandra guarda el historial de actividad, sesiones de juego, tiempo jugado y logros. Son muchísimos registros que crecen todos los días y que casi siempre se leen por usuario o por juego, ordenados por fecha, que es justo donde Cassandra rinde mejor.

### Instalar dependencias
```
pip install -r requirements.txt
```

### Levantar Cassandra
```
docker run --name cassandra -p 9042:9042 -d cassandra:4.1
```
Cassandra tarda como un minuto en arrancar. Se puede revisar si ya está lista con `docker exec cassandra nodetool status` (debe aparecer `UN`).

### Cargar datos
Desde la carpeta principal del proyecto:
```
python populate.py
```

### Ejecutar las consultas
Para acceder al menú de consultas se debe ejecutar el archivo main.py
```
python main.py
```
Se tendrá un menú que permitirá seleccionar a qué base de datos se desa acceder, y después un menú que contiene todas las consultas diseñadas para esa base de datos


## Cassandra
Todo lo de Cassandra está en la carpeta `Cassandra/`:
- `schema.cql`: las 7 tablas del keyspace `game_activity`.
- `schema.py`: crea las tablas leyendo `schema.cql`.
- `populate_cassandra.py`: genera las sesiones y logros y los inserta en todas las tablas.
- `queries.py`: las 8 consultas, una función por requerimiento.

| Opción | Consulta | Tabla | Partition key | Clustering key |
|---|---|---|---|---|
| 1 | Últimas 20 sesiones de un usuario | sessions_by_user | user_id | session_start DESC |
| 2 | Sesiones de un usuario entre dos fechas | sessions_by_user | user_id | session_start DESC |
| 3 | Sesiones de un usuario con un juego | sessions_by_user_game | user_id, game_id | session_start DESC |
| 4 | Minutos jugados por día en un mes | playtime_by_user_day | user_id, month | play_date ASC |
| 5 | Últimas 100 sesiones de un juego en un día | sessions_by_game_day | game_id, play_date | session_start DESC, user_id |
| 6 | Últimos 30 logros de un usuario | achievements_by_user | user_id | unlocked_at DESC, achievement_id |
| 7 | Últimas 25 sesiones en una plataforma | sessions_by_user_platform | user_id, platform | session_start DESC |
| 8 | Actividad por hora de un juego en un día | activity_by_game_hour | game_id, play_date | hour ASC |

Las sesiones se generan a partir de `data/played.json` y `data/games.json`, así coinciden con lo que hay en Dgraph y MongoDB. Si esos archivos todavía no existen, el script arma una muestra pequeña directo de `data/games.csv` para poder probar.

Cada sesión se escribe en las 4 tablas de sesiones (desnormalización) y los totales de las tablas 4 y 8 se calculan en el script antes de insertar, porque Cassandra no está pensada para sumar al consultar. Para insertar rápido se usan prepared statements y `execute_concurrent_with_args`, y todas las consultas usan la partition key completa, así que ninguna necesita `ALLOW FILTERING`.

En el menú cada consulta sugiere un valor de ejemplo que sí existe en la base. Basta con presionar Enter para usarlo.
