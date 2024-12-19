import sqlite3


def DB_init():
    connection = sqlite3.connect('requests.db')
    cursor = connection.cursor()
    cursor.execute("""                   
    CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY,
    id_user TEXT NOT NULL,
    film TEXT NOT NULL,
    date timestamp)""")
    connection.commit()
    connection.close()
