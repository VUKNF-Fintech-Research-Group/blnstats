import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
import os


DEFAULT_DB_HOST = 'blnstats-mysql'
DEFAULT_DB_NAME = 'lnstats'
DEFAULT_DB_USER = 'lnstats'
DEFAULT_DB_PASSWORD = 'lnstats'



def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', DEFAULT_DB_HOST),
        database=os.getenv('DB_NAME', DEFAULT_DB_NAME),
        user=os.getenv('DB_USER', DEFAULT_DB_USER),
        password=os.getenv('DB_PASSWORD', DEFAULT_DB_PASSWORD)
    )
    conn.cursor_class = MySQLCursorDict
    return conn



def create_database_if_not_exists(db_name):
    try:
        # Establish a connection to MySQL (connect to server, not to a specific database yet)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', DEFAULT_DB_HOST),
            user=os.getenv('DB_USER', DEFAULT_DB_USER),
            password=os.getenv('DB_PASSWORD', DEFAULT_DB_PASSWORD)
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f" CREATE DATABASE IF NOT EXISTS {db_name} ")
            
            print(f"Database `{db_name}` created or already exists.")
            
            # Clean up
            cursor.close()
            connection.close()

    except Exception as e:
        print(f"Error: '{e}'")





def create_tables_if_not_exists(db_conn):
    '''
    CREATE TABLE IF NOT EXISTS `Lightning_Channels` (
        `ShortChannelID` BIGINT NOT NULL,
        `BlockIndex` INT NOT NULL,
        `TxIndex` INT NOT NULL,
        `OutputIndex` INT NOT NULL,
        `NodeID1` CHAR(66) NOT NULL,
        `NodeID2` CHAR(66) NOT NULL,
        PRIMARY KEY (`ShortChannelID`),
        INDEX idx_node_id_1 (`NodeID1`),
        INDEX idx_node_id_2 (`NodeID2`),
        INDEX idx_blockindex_txindex (`BlockIndex`, `TxIndex`)
    );
    '''
    '''
    CREATE TABLE IF NOT EXISTS `System_Users` (
        `ID` INT NOT NULL AUTO_INCREMENT,
        `Email` VARCHAR(255) NOT NULL,
        `Password` VARCHAR(255) NOT NULL,
        `Admin` TINYINT(1) NOT NULL DEFAULT 0,
        `Enabled` TINYINT(1) NOT NULL DEFAULT 1,
        `LastSeen` VARCHAR(255) NOT NULL DEFAULT '',
        PRIMARY KEY (`ID`)
    );
    '''
    pass


