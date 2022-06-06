import os

DB_NAME = os.path.join(os.getcwd(), 'db', 'save_data.db')

MAKE_DB = """CREATE TABLE IF NOT EXISTS preservation(
           id INTEGER PRIMARY KEY AUTOINCREMENT
             NOT NULL
             UNIQUE,
           path STRING,
           text STRING,
           note STRING,
           hashIm STRING);"""

LOAD_SAVES = '''SELECT note, hashIm FROM preservation'''

DELETE_IM = '''DELETE from preservation where hashIm = :hashIm'''

GET_IMAGE = '''SELECT path FROM preservation 
                                    WHERE hashIm = :hashIm'''

GET_NOTE = '''SELECT text FROM preservation 
                    WHERE id = (SELECT id FROM preservation 
                    WHERE note = :note)'''
GET_SAVES = '''INSERT INTO preservation (path, text, note, hashIm)
                                            VALUES (?, ?, ?, ?)'''
