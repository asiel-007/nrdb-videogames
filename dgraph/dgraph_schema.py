from pydgraph import DgraphClient, Operation


def create_schema(client: DgraphClient):
    """
    Creación de schema definido
    """
    schema = """
    user_id: string @index(exact) .
    username: string @index(hash) .
    game_id: string @index(exact) .
    title: string .
    release_year: int .
    average_rating: float .
    total_players: int @index(int) .
    genre_id: string .
    genre_name: string .
    dev_id: string .
    dev_name: string .
    played: [uid] @reverse .
    favorite: bool .
    rating: float .
    follows: [uid] @reverse .
    belongs_to_genre [uid] @reverse .
    developed_by [uid] @reverse .
    similar_to [uid] @reverse .
    type User {
        user_id
        username
        played
        follows
    }
    type Game {
        game_id
        title
        release_year
        average_rating
        total_players
        belongs_to_genre
        developed_by
        similar_to
    }
    type Genre {
        genre_id
        genre_name
    }
    type Developer {
        dev_id
        dev_name
    }
    """
    try:
        client.alter(Operation(schema=schema))
    except Exception as e:
        print(f"Error al crear schema de Dgraph: {e}")
