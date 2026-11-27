from connect import connect_cassandra, connect_dgraph, connect_mongo
from Cassandra import queries as cq

def print_rows(rows):
    # imprime los resultados como una tabla sencilla
    if not rows:
        print("no hay resultados\n")
        return
    columns = rows[0]._fields
    print(" | ".join(columns))
    print("-" * 80)
    for row in rows:
        print(" | ".join(str(value) for value in row))
    print(f"\n{len(rows)} filas\n")


def ask(text, default):
    # pide un valor y si se deja vacio usa el de ejemplo
    value = input(f"{text} [{default}]: ").strip()
    return value or default


def cassandra_menu(session):
    if session is None:
        print("no hay conexion con cassandra")
        return

    # valores de ejemplo que si existen en la base, para no tener que adivinar
    sample = cq.sample_values(session) or {
        "user_id": "u_0001", "game_id": "g_0001", "platform": "PC",
        "date": "2026-10-15", "month": "2026-10",
    }

    while True:
        try:
            op = int(input("""Select a query:
        1. Last 20 game sessions of a user
        2. User sessions within a date range
        3. User session history for a specific game
        4. Daily playtime of a user during a month
        5. Last 100 sessions of a game on a specific date
        6. Last 30 achievements unlocked by a user
        7. Last 25 sessions of a user on a specific platform
        8. Hourly activity of a game on a specific day
        9. Return\n"""))
        except ValueError:
            print("Invalid option")
            continue

        try:
            if op == 1:
                user_id = ask("user_id", sample["user_id"])
                print_rows(cq.last_sessions(session, user_id))
            elif op == 2:
                user_id = ask("user_id", sample["user_id"])
                start = ask("start date (YYYY-MM-DD)", "2026-09-01")
                end = ask("end date (YYYY-MM-DD)", "2026-09-30")
                print_rows(cq.sessions_in_range(session, user_id, start, end))
            elif op == 3:
                user_id = ask("user_id", sample["user_id"])
                game_id = ask("game_id", sample["game_id"])
                print_rows(cq.sessions_by_game(session, user_id, game_id))
            elif op == 4:
                user_id = ask("user_id", sample["user_id"])
                month = ask("month (YYYY-MM)", sample["month"])
                print_rows(cq.playtime_by_day(session, user_id, month))
            elif op == 5:
                game_id = ask("game_id", sample["game_id"])
                date = ask("date (YYYY-MM-DD)", sample["date"])
                print_rows(cq.game_sessions_on_date(session, game_id, date))
            elif op == 6:
                user_id = ask("user_id", sample["user_id"])
                print_rows(cq.last_achievements(session, user_id))
            elif op == 7:
                user_id = ask("user_id", sample["user_id"])
                platform = ask("platform", sample["platform"])
                print_rows(cq.sessions_by_platform(session, user_id, platform))
            elif op == 8:
                game_id = ask("game_id", sample["game_id"])
                date = ask("date (YYYY-MM-DD)", sample["date"])
                print_rows(cq.activity_by_hour(session, game_id, date))
            elif op == 9:
                break
            else:
                print("Invalid option")
        except ValueError:
            # pasa cuando la fecha no tiene el formato correcto
            print("formato de fecha incorrecto\n")


def mongo_menu():
    while True:
        op = int(input("""Select a query:
        1. Search games by genre
        2. Search games by platform
        3. Top rated games
        4. Games by developer
        5. Games by age rating
        6. Average price per platform
        7. Games with multiplayer mode
        8. PC games by minimum RAM requirement
        9. Return\n"""))
        if op == 1:
            print("Search games by genre")
            pass
        elif op == 2:
            print("Search games by platform")
            pass
        elif op == 3:
            print("Top rated games")
            pass
        elif op == 4:
            print("Games by developer")
            pass
        elif op == 5:
            print("Games by age rating")
            pass
        elif op == 6:
            print("Average price per platform")
            pass
        elif op == 7:
            print("Games with multiplayer mode")
            pass
        elif op == 8:
            print("PC games by minimum RAM requirement")
            pass
        elif op == 9:
            break
        else:
            print("Invalid option")


def dgraph_menu():
    while True:
        op = int(input("""Select a query:
        1. Games liked by people I follow
        2. Similar games
        3. Recommendations by favorite genre
        4. Follow suggestions
        5. Who played this also played
        6. Genres played by friends but not by me
        7. More games from liked developers
        8. People I follow and play this game
        9. Return\n"""))
        if op == 1:
            print("Games liked by people I follow")
            pass
        elif op == 2:
            print("Similar games")
            pass
        elif op == 3:
            print("Recommendations by favorite genre")
            pass
        elif op == 4:
            print("Follow suggestions")
            pass
        elif op == 5:
            print("Who played this also played")
            pass
        elif op == 6:
            print("Genres played by friends but not by me")
            pass
        elif op == 7:
            print("More games from liked developers")
            pass
        elif op == 8:
            print("People i follow and play this game")
            pass
        elif op == 9:
            break
        else:
            print("Invalid option")


def main():
    cassandra_session = None
    try:
        dgraph_client = connect_dgraph()
    except Exception as e:
        print(f"Error connecting to Dgraph: {e}")
    try:
        cassandra_session = connect_cassandra()
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}")
    try:
        mongo_db = connect_mongo()
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
    while True:
        op = int(input("""Select :
        1. Sessions, activity and achievements
        2. Detailed videogame catalog
        3. Videogame recommendation
        4. Exit\n"""))
        if op == 1:
            cassandra_menu(cassandra_session)
        elif op == 2:
            mongo_menu()
        elif op == 3:
            dgraph_menu()
        elif op == 4:
            break


if __name__ == "__main__":
    main()
