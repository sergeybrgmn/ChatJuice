"""I/O to database"""
import os
from typing import Dict, List, Tuple

import sqlite3

conn = sqlite3.connect("juice.db")
cursor = conn.cursor()

def insert(table: str, column_values: Dict) -> int:
    """Universal method to insert data in any table."""
    columns = ', '.join( column_values.keys() )
    values = tuple(column_values.values())
    placeholders = ", ".join( "?" * len(column_values.keys()) )
    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    last_id = cursor.lastrowid
    return last_id

def update_value(table: str, index: int, column_value: Tuple) -> int:
    """method to update the data in the table"""
    column = column_value[0]
    value = column_value[1]
    cursor.execute(f"UPDATE {table} " 
                   f"SET {column} = '{value}' "
                   f"WHERE external_user_id = {index}"
                   )
    conn.commit()

def fetch_value(table: str, index: int, column: str):
    cursor.execute(
        f"SELECT {column} FROM {table} WHERE external_user_id = ?",
        (index,))
    row = cursor.fetchall()
    return row[0][0]

def check_id(table: str, col: str, val: str) -> int:
    cursor.execute(
        f"SELECT id FROM {table} WHERE {col} = ?",
        (val,))
    row = cursor.fetchall()
    if len(row)==0:
        id = 0
    else:
        id = row[0][0]
    return id

def _init_db():
    """Init DB"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()

def check_db_exists():
    """Check DB, init if not yet"""

    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='users'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()

check_db_exists()