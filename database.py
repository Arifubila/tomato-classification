import sqlite3
import os
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# CREATE TABLE
# ============================================================

def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    # ========================================================
    # TABLE HISTORY
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT,

            hue REAL,

            saturation REAL,

            value REAL,

            prediction TEXT,

            confidence REAL,

            process_time REAL,

            created_at TEXT

        )
    """)

    # ========================================================
    # TABLE MONITORING
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nama_tomat TEXT NOT NULL,

            filename TEXT,

            tanggal_mulai TEXT NOT NULL,

            status TEXT NOT NULL,

            tanggal_busuk TEXT,

            keterangan TEXT,

            created_at TEXT

        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# INSERT HISTORY
# ============================================================

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

    created_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

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


# ============================================================
# INSERT MONITORING
# ============================================================

def insert_monitoring(
    nama_tomat,
    filename,
    tanggal_mulai,
    status,
    tanggal_busuk=None,
    keterangan=""
):

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cursor.execute("""
        INSERT INTO monitoring
        (
            nama_tomat,
            filename,
            tanggal_mulai,
            status,
            tanggal_busuk,
            keterangan,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nama_tomat,
        filename,
        tanggal_mulai,
        status,
        tanggal_busuk,
        keterangan,
        created_at
    ))

    conn.commit()
    conn.close()


# ============================================================
# GET MONITORING
# ============================================================

def get_monitoring():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM monitoring
        ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


# ============================================================
# GET SINGLE MONITORING
# ============================================================

def get_monitoring_by_id(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM monitoring
        WHERE id = ?
    """, (id,))

    data = cursor.fetchone()

    conn.close()

    return data


# ============================================================
# UPDATE MONITORING
# ============================================================

def update_monitoring(
    id,
    status,
    tanggal_busuk=None,
    keterangan=""
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE monitoring
        SET
            status = ?,
            tanggal_busuk = ?,
            keterangan = ?
        WHERE id = ?
    """, (
        status,
        tanggal_busuk,
        keterangan,
        id
    ))

    conn.commit()
    conn.close()


# ============================================================
# DELETE MONITORING
# ============================================================

def delete_monitoring(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM monitoring
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()