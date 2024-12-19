import sqlite3, datetime

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



def Insert_to_DB(id_user: str, film_name: str) -> None:
    connection = sqlite3.connect('requests.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO requests (id_user, film, date) VALUES (?, ?, ?)',
                    (id_user, film_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    connection.commit()
    connection.close()

DB_init()
Insert_to_DB('123', '232131')