import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT,

            hue REAL,

            saturation REAL,

            value REAL,

            prediction TEXT,

            confidence REAL,

            process_time REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


def insert_history(
    filename,
    h,
    s,
    v,
    prediction,
    confidence,
    process_time
):

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%d-%m-%Y")

    cursor.execute("""
        INSERT INTO history
        (
            filename,
            hue,
            saturation,
            value,
            prediction,
            confidence,
            process_time,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        h,
        s,
        v,
        prediction,
        confidence,
        process_time,
        created_at
    ))

    conn.commit()
    conn.close()