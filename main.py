from connect import connect_cassandra, connect_dgraph

def cassandra_menu():
    while True:
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
        if op == 1:
            print("Last 20 game sessions of a user (table: sessions_by_user) - not implemented yet")
        elif op == 2:
            print("User sessions within a date range (table: sessions_by_user) - not implemented yet")
        elif op == 3:
            print("User session history for a specific game (table: sessions_by_user_game) - not implemented yet")
        elif op == 4:
            print("Daily playtime of a user during a month (table: playtime_by_user_day) - not implemented yet")
        elif op == 5:
            print("Last 100 sessions of a game on a specific date (table: sessions_by_game_day) - not implemented yet")
        elif op == 6:
            print("Last 30 achievements unlocked by a user (table: achievements_by_user) - not implemented yet")
        elif op == 7:
            print("Last 25 sessions of a user on a specific platform (table: sessions_by_user_platform) - not implemented yet")
        elif op == 8:
            print("Hourly activity of a game on a specific day (table: activity_by_game_hour) - not implemented yet")
        elif op == 9:
            break
        else:
            print("Invalid option")


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
    try:
        dgraph_client = connect_dgraph()
    except Exception as e:
        print(f"Error connecting to Dgraph: {e}")
    try:
        cassandra_session = connect_cassandra()
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}")
    while True:
        op = int(input("""Select :
        1. Sessions, activity and achievements
        2. Detailed videogame catalog
        3. Videogame recommendation
        4. Exit\n"""))
        if op == 1:
            cassandra_menu()
        elif op == 2:
            mongo_menu()
        elif op == 3:
            dgraph_menu()
        elif op == 4:
            break


if __name__ == "__main__":
    main()
