import sqlite3

DB_PATH = "database/enlish.db"

def get_connection():
    return sqlite3.connect(DB_PATH)