import json
from datetime import datetime
import gzip
import requests
from ..database.utils import get_db_connection
import hashlib




class LNDDBReader:
    """
    Class for importing LND DBReader data into the database.

    This class is designed to handle the parsing and storage of LND DBReader data,
    which contains data related to the Lightning Network such as channel announcements,
    node announcements, and node addresses.
    """


    def __init__(self, file_path):
        """
        Initializes the LNDDBReader class with the path to the LND DBReader data.

        :param file_path: str - Path to the LND DBReader data (local file or URL).
        """
        self.file_path = file_path

        if(file_path.startswith('http')):
            print(f"[*] Downloading LND DBReader data from '{file_path}'")
            self.file_path = self.__download_data(file_path)

        print(f"[*] Reading LND DBReader data from '{self.file_path}'")
        self.data = self.__read_file()

        print("[*] Creating tables if not exists")
        self.create_tables_if_not_exists()

        print("[*] Writing data to database")
        self.import_data()

        print("[*] Inserting data into main system table (DB Table: Lightning_Channels)")
        self.insert_or_ignore_into_main()

        print("[*] Done importing LND DBReader data")




    def __download_data(self, url):
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        addressHashID = hashlib.sha256(url.encode()).hexdigest()[:8].upper()
        timeNow = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_path = f"/DATA/INPUT/lnd-dbreader-{addressHashID}--{timeNow}"
        if(self.file_path.endswith('.gz')):
            with open(f"{file_path}.json.gz", 'wb') as file:
                file.write(response.content)
                return f"{file_path}.json.gz"
        else:
            with open(f"{file_path}.json", 'wb') as file:
                file.write(response.content)
                return f"{file_path}.json"



    def __read_file(self):
        if(self.file_path.endswith('.gz')):
            with gzip.open(self.file_path, 'rt') as file:
                return json.load(file)['data']
        else:
            with open(self.file_path, 'r') as file:
                return json.load(file)['data']  



    def create_tables_if_not_exists(self):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `_LND_DBReader_ChannelAnnouncement` (
                        `ShortChannelID` BIGINT NOT NULL,
                        `BlockIndex` INT NOT NULL,
                        `TxIndex` INT NOT NULL,
                        `OutputIndex` INT NOT NULL,
                        `NodeID1` CHAR(66) NOT NULL,
                        `NodeID2` CHAR(66) NOT NULL,
                        CONSTRAINT `PRIMARY` PRIMARY KEY (`ShortChannelID`),
                        CONSTRAINT `idx_ShortChannelID` UNIQUE (`ShortChannelID`)
                    );
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `_LND_DBReader_NodeAnnouncements` ( 
                        `ID` INT AUTO_INCREMENT NOT NULL,
                        `NodeID` CHAR(66) NOT NULL,
                        `Alias` VARCHAR(32) NOT NULL,
                        `FirstSeen` INT NOT NULL,
                        `LastSeen` INT NOT NULL,
                        CONSTRAINT `PRIMARY` PRIMARY KEY (`ID`),
                        CONSTRAINT `unique_nodeid_alias` UNIQUE (`NodeID`, `Alias`)
                    );
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `_LND_DBReader_NodeAddresses` ( 
                        `ID` INT AUTO_INCREMENT NOT NULL,
                        `NodeID` CHAR(66) NOT NULL,
                        `Address` VARCHAR(255) NOT NULL,
                        `Port` INT NOT NULL,
                        `FirstSeen` INT NOT NULL,
                        `LastSeen` INT NOT NULL,
                        CONSTRAINT `PRIMARY` PRIMARY KEY (`ID`),
                        CONSTRAINT `unique_nodeid_address_port` UNIQUE (`NodeID`, `Address`, `Port`)
                    );
                ''')
                conn.commit()



    def import_data(self):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                print("[*] Inserting channel announcements into _LND_DBReader_ChannelAnnouncement table (INSERT OR IGNORE)")
                for item in self.data['channel_announcements']:

                    short_channel_id = item['ShortChannelID']
                    block_height = (short_channel_id >> 40) & 0xFFFFFF
                    tx_index = (short_channel_id >> 16) & 0xFFFFFF
                    output_index = short_channel_id & 0xFFFF

                    node_id_1 = item['NodeID1']
                    node_id_2 = item['NodeID2']

                    cursor.execute('''
                        INSERT IGNORE INTO _LND_DBReader_ChannelAnnouncement 
                            (ShortChannelID, BlockIndex, TxIndex, OutputIndex, NodeID1, NodeID2) VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (short_channel_id, block_height, tx_index, output_index, node_id_1, node_id_2))
                conn.commit()


                print("[*] Inserting node announcements into _LND_DBReader_NodeAnnouncements table (INSERT OR UPDATE)")
                for item in self.data['node_announcements']:
                    node_id = item['NodeID']
                    alias = item['Alias']
                    first_seen = item['FirstSeen']
                    last_seen = item['LastSeen']

                    cursor.execute('''
                        INSERT INTO _LND_DBReader_NodeAnnouncements
                            (NodeID, Alias, FirstSeen, LastSeen) VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            FirstSeen = LEAST(FirstSeen, VALUES(FirstSeen)),
                            LastSeen = GREATEST(LastSeen, VALUES(LastSeen))
                    ''', (node_id, alias, first_seen, last_seen))
                conn.commit()


                print("[*] Inserting node addresses into _LND_DBReader_NodeAddresses table (INSERT OR UPDATE)")
                for item in self.data['node_addresses']:
                    node_id = item['NodeID']
                    address = item['Address']
                    port = item['Port']
                    first_seen = item['FirstSeen']
                    last_seen = item['LastSeen']

                    cursor.execute('''
                        INSERT INTO _LND_DBReader_NodeAddresses
                            (NodeID, Address, Port, FirstSeen, LastSeen) VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            FirstSeen = LEAST(FirstSeen, VALUES(FirstSeen)),
                            LastSeen = GREATEST(LastSeen, VALUES(LastSeen))
                    ''', (node_id, address, port, first_seen, last_seen))
                conn.commit()



    def insert_or_ignore_into_main(self):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT IGNORE INTO Lightning_Channels 
                    (ShortChannelID, BlockIndex, TxIndex, OutputIndex, NodeID1, NodeID2)
                    SELECT 
                        ca.ShortChannelID,
                        ca.BlockIndex,
                        ca.TxIndex,
                        ca.OutputIndex,
                        ca.NodeID1,
                        ca.NodeID2
                    FROM _LND_DBReader_ChannelAnnouncement ca
                ''')
                conn.commit()

