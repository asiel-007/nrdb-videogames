# CASSANDRA


# MONGODB


# DGRAPH
"""
para poblar la base de datos de dgraph se leerá el archivo data/vgsales.csv, que contiene las columnas:
Name,Platform,Year,Genre,Publisher
Se seleccionarán renglones de forma aleatoria en el archivo, y se extraerán los datos de estas columnas para insertar
los nodos de Game, Developer y Genre, utilizando los datos de la siguiente forma:
Game {
    title: Name
    platform: Platform
    release_year: Year
}

Genre {
    name: Genre
}

Developer {
    name: Publisher
}

Los campos de total_players y average_rating para el tipo de nodo Game serán generados de forma aleatoria.
Las relaciones BELONGS_TO_GENRE y DEVELOPED_BY serán creadas al mismo tiempo que se inserten todos los datos de cada
videojuego, comprobando si el nodo Developer y Genre ya fueron creados o si deben crearse.
"""
