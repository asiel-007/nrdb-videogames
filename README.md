# Recomendación de videojuegos
Integrantes del equipo:
- Axel Vázquez - 759603
- Daniel Jiménez - 756045
- Haziel Murillo - 757186

La idea es una plataforma web donde los jugadores pueden explorar un catálogo de videojuegos, ver la ficha de cada juego, revisar su propio historial de juego y recibir recomendaciones de qué jugar después. Dentro de la app el usuario podrá buscar juegos por nombre, género o plataforma, ver algunas estadísticas del catálogo (por ejemplo, qué géneros tienen mejor calificación o cuánto cuestan los juegos en cada consola), consultar cuánto y cuándo ha jugado, y ver qué juegan las personas que sigue.  
MongoDB guarda el catálogo, es decir juegos, géneros, plataformas, precios, idiomas, requisitos y demás metadatos. Cada juego trae información un poco distinta (uno de PC tiene requisitos de sistema, uno de consola no), así que los documentos flexibles nos acomodan muy bien. Dgraph guarda las conexiones, quién sigue a quién, quién jugó o marcó como favorito qué juego, a qué géneros pertenece cada juego, quién lo desarrolló y qué juegos se parecen entre sí, y de estas relaciones salen las recomendaciones. Cassandra guarda el historial de actividad, sesiones de juego, tiempo jugado y logros. Son muchísimos registros que crecen todos los días y que casi siempre se leen por usuario o por juego, ordenados por fecha, que es justo donde Cassandra rinde mejor.

### Cargar datos
```
cd data
python populate.py
```

### Ejecutar las consultas
Para acceder al menú de consultas se debe ejecutar el archivo main.py
```
python main.py
```
Se tendrá un menú que permitirá seleccionar a qué base de datos se desa acceder, y después un menú que contiene todas las consultas diseñadas para esa base de datos
