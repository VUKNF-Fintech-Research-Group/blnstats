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





def create_tables_if_not_exists():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `Blockchain_Blocks` ( 
                    `BlockHeight` INT UNSIGNED NOT NULL,
                    `BlockHash` CHAR(64) NOT NULL,
                    `Timestamp` INT UNSIGNED NOT NULL,
                    `Time` DATETIME NOT NULL,
                    `Date` DATE NOT NULL,
                    PRIMARY KEY (`BlockHeight`),
                    CONSTRAINT `BlockHeight` UNIQUE (`BlockHeight`),
                    INDEX `idx_BlockHash` (`BlockHash`),
                    INDEX `idx_Date` (`Date`),
                    INDEX `idx_Timestamp` (`Timestamp`)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `Blockchain_Transactions` ( 
                    `ShortChannelID` BIGINT UNSIGNED NOT NULL,
                    `FundingBlockIndex` INT UNSIGNED NOT NULL,
                    `FundingTxIndex` INT UNSIGNED NOT NULL,
                    `FundingOutputIndex` SMALLINT UNSIGNED NOT NULL,
                    `FundingTxID` CHAR(64) NOT NULL,
                    `FundingScriptHash` CHAR(64) NOT NULL,
                    `Value` BIGINT UNSIGNED NOT NULL,
                    `SpendingBlockIndex` INT UNSIGNED NOT NULL,
                    `SpendingTxID` CHAR(64) NOT NULL,
                    `UpdatedDate` DATE NOT NULL,
                    PRIMARY KEY (`ShortChannelID`),
                    INDEX `idx_Funding_SpendingBlockIndex` (`FundingBlockIndex`, `SpendingBlockIndex`),
                    INDEX `idx_funding_spending_value_covering` (`FundingBlockIndex`, `SpendingBlockIndex`, `Value`),
                    INDEX `idx_Value` (`Value`)
                )
            ''')

            cursor.execute('''
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
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `Lightning_Entities` ( 
                    `NodeID` CHAR(66) NOT NULL,
                    `EntityName` CHAR(255) NOT NULL,
                    PRIMARY KEY (`NodeID`)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `Lightning_NodeAliases` ( 
                    `ID` INT AUTO_INCREMENT NOT NULL,
                    `NodeID` CHAR(66) NOT NULL,
                    `Alias` VARCHAR(32) NOT NULL,
                    `firstSeen` TIMESTAMP NULL,
                    `lastSeen` TIMESTAMP NULL,
                    PRIMARY KEY (`ID`),
                    CONSTRAINT `unique_nodeid_alias` UNIQUE (`NodeID`, `Alias`),
                    INDEX `idx_alias` (`Alias`),
                    INDEX `idx_nodeid` (`NodeID`)
                );
            ''')





            # System Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `System_Users` (
                    `ID` INT NOT NULL AUTO_INCREMENT,
                    `Email` VARCHAR(255) NOT NULL UNIQUE,
                    `Password` VARCHAR(255) NOT NULL,
                    `Admin` TINYINT(1) NOT NULL DEFAULT 0,
                    `Enabled` TINYINT(1) NOT NULL DEFAULT 1,
                    `LastSeen` TIMESTAMP NULL DEFAULT NULL,
                    `CreatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `UpdatedAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`ID`)
                );
            ''')

            # Insert Default User if table is empty
            cursor.execute('SELECT COUNT(*) FROM System_Users')
            result = cursor.fetchone()[0]
            if result == 0:
                cursor.execute('INSERT INTO System_Users (Email, Password, Admin, Enabled) VALUES (%s,%s,%s,%s)',
                               ('admin@admin.com', '$2a$12$/ZIb.Mw5ZEPlPdqNkC3A3.O9hySEuhrt2FpaU9y1iMWVVW4RYTIW2', 1, 1))
            conn.commit()


