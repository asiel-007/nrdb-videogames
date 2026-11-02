from connect import connect_dgraph

def cassandra_menu():
    while True:
        op = int(input("""Select a query:
        1.
        2.
        3.
        4.
        5.
        6.
        7.
        8.
        9 Return\n"""))
        if op == 1:
            pass
        elif op == 2:
            pass
        elif op == 3:
            pass
        elif op == 4:
            pass
        elif op == 5:
            pass
        elif op == 6:
            pass
        elif op == 7:
            pass
        elif op == 8:
            pass
        elif op == 9:
            break
        else:
            print("Invalid option")


def mongo_menu():
    while True:
        op = int(input("""Select a query:
        1.
        2.
        3.
        4.
        5.
        6.
        7.
        8.
        9. Return\n"""))
        if op == 1:
            pass
        elif op == 2:
            pass
        elif op == 3:
            pass
        elif op == 4:
            pass
        elif op == 5:
            pass
        elif op == 6:
            pass
        elif op == 7:
            pass
        elif op == 8:
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
        print(f"Error connecting to db: {e}")
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
