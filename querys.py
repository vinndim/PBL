DB_NAME = 'save_data.db'

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
