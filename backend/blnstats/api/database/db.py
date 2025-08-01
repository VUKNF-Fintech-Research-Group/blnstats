############################################################
# Author:           Tomas Vanagas
# Updated:          2025-06-29
# Version:          1.0
# Description:      Database connection
############################################################


import sqlite3


def get_db_connection(filename='/app/db.sqlite3'):
    conn = sqlite3.connect(filename)
    conn.row_factory = sqlite3.Row
    return conn