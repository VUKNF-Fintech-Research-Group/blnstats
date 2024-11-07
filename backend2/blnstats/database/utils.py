import mysql.connector
from mysql.connector.cursor import MySQLCursorDict




def get_db_connection():
    conn = mysql.connector.connect(
        host='blnstats-mysql',
        database='lnstats',
        user='lnstats',
        password='lnstats'
    )
    conn.cursor_class = MySQLCursorDict
    return conn



def create_database_if_not_exists(db_name):
    try:
        # Establish a connection to MySQL (connect to server, not to a specific database yet)
        connection = mysql.connector.connect(
            host='blnstats-mysql',
            user='lnstats',
            password='lnstats'
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
        INDEX idx_blockchain_height (`BlockIndex`),
        INDEX idx_node_id_1 (`NodeID1`),
        INDEX idx_node_id_2 (`NodeID2`)
    );
    '''


    pass


