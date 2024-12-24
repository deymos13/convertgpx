import os
import sqlite3

def create_database():# Настройка базы данных SQLite для хранения пользователей
    if not os.path.exists("./database/database.db"):
        conn = sqlite3.connect("./database/database.db")
        cursor = conn.cursor()
        # Создаём таблицу, если её ещё нет
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)")
        conn.commit()
        conn.close()