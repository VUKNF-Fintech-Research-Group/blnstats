import bz2
from pyln.proto.primitives import varint_decode
import base64
from ..database.utils import get_db_connection
import requests
import os


LATEST_LN_RESEARCH_DOWNLOAD_URL = "https://storage.googleapis.com/lnresearch/gossip-20230924.gsp.bz2"


class LNResearchData:
    """
    Class for importing LN Research dataset into the database.

    This class is designed to handle the parsing and storage of LN Research dataset files,
    which contain data related to the Lightning Network such as channel announcements,
    node announcements, and channel updates.
    """
    file_path = LATEST_LN_RESEARCH_DOWNLOAD_URL


    def __init__(self, file_path : str = None):
        """
        Initializes the LNResearchData class with the path to the LN Research dataset file.

        :param file_path: str - Path to the LN Research dataset file (URL or local path).
        """
        
        if(file_path != None):
            self.file_path = file_path

        if(self.file_path.startswith('http')):
            print(f"[*] Downloading LN Research dataset from '{self.file_path}'")
            self.file_path = self.__download_data(self.file_path)

        print(f"[*] Creating tables if not exists")
        self.__create_tables_if_not_exists()

        print(f"[*] Importing LN Research dataset from '{self.file_path}' into _LNResearch_XXXX DB tables")
        self.__import_data(self.file_path)

        print("[*] Inserting data into main system table (DB Table: Lightning_Channels)")
        self.insert_or_ignore_into_main()

        print("[*] Done importing LN Research data")



    def __download_data(self, url):
        """
        Downloads the LN Research dataset from the given URL and saves it to the local filesystem.

        :param url: str - URL of the LN Research dataset file.
        :return: str - Path to the downloaded file.
        """
        
        file_path = f"/DATA/INPUT/{url.split('/')[-1]}"
        if(os.path.exists(file_path)):
            print(f"[*] File already exists at '{file_path}'")
            return file_path
        
        # Only download if file doesn't exist
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(file_path+'_tmp', 'wb') as file:
            file.write(response.content)
        os.rename(file_path+'_tmp', file_path)
        return file_path





    def __parse_message(self, db_cursor, msg: bytes):
        # Extract the message type from the first two bytes
        msg_type = int.from_bytes(msg[:2], byteorder='big')

        # Channel Announcement
        if msg_type == 256:
            features_len = int.from_bytes(msg[258:260], byteorder='big')
            features = msg[260:260+features_len].hex()
            chain_hash = msg[260+features_len:292+features_len].hex()
            short_channel_id = int.from_bytes(msg[292+features_len:300+features_len], byteorder='big')
            block_height = (short_channel_id >> 40) & 0xFFFFFF
            tx_index = (short_channel_id >> 16) & 0xFFFFFF
            output_index = short_channel_id & 0xFFFF
            node_id_1 = msg[300+features_len:333+features_len].hex()
            node_id_2 = msg[333+features_len:366+features_len].hex()
            bitcoin_key_1 = msg[366+features_len:399+features_len].hex()
            bitcoin_key_2 = msg[399+features_len:432+features_len].hex()

            db_cursor.execute(f'''
                INSERT IGNORE INTO _LNResearch_ChannelAnnouncements 
                    (ShortChannelID, BlockIndex, TxIndex, OutputIndex, NodeID1, NodeID2) VALUES (%s, %s, %s, %s, %s, %s)
            ''', [
                short_channel_id,
                block_height,
                tx_index,
                output_index,
                node_id_1,
                node_id_2
            ])



        # Node Announcement
        elif msg_type == 257:
            signature = msg[2:66].hex()
            features_len = int.from_bytes(msg[66:68], byteorder='big')
            features = msg[68:68+features_len].hex()
            timestamp = int.from_bytes(msg[68+features_len:72+features_len], byteorder='big')
            node_id = msg[72+features_len:105+features_len].hex()
            rgb_color = msg[105+features_len:108+features_len].hex()
            alias = msg[108+features_len:140+features_len].decode('utf-8', errors='ignore').rstrip('\x00')
            addrlen = int.from_bytes(msg[140+features_len:142+features_len], byteorder='big')
            addresses = msg[142+features_len:142+features_len+addrlen].hex()
            addresses_data = msg[142+features_len:142+features_len+addrlen]
            parsed_addresses = self.__parse_addresses(addresses_data)

            db_cursor.execute(f'''
                INSERT INTO _LNResearch_NodeAnnouncements
                    (NodeID, Alias, FirstSeen, LastSeen) VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    FirstSeen = LEAST(FirstSeen, VALUES(FirstSeen)),
                    LastSeen = GREATEST(LastSeen, VALUES(LastSeen))
            ''', [
                node_id,
                alias,
                timestamp,
                timestamp
            ])

            addressID = 0
            for parsed_address in parsed_addresses:
                nodeAddress = parsed_address[0]
                nodePort = parsed_address[1]
                addressType = ''
                if ':' in nodeAddress:
                    addressType = 'IPv6'
                elif '.' in nodeAddress:
                    addressType = 'IPv4'
                elif len(nodeAddress) == 20:
                    nodeAddress = self.__hex_to_onion(nodeAddress)
                    addressType = 'Tor v2'
                elif len(nodeAddress) == 70:
                    nodeAddress = self.__hex_to_onion(nodeAddress)
                    addressType = 'Tor v3'

                # INSERT OR UPDATE
                db_cursor.execute(f'''
                    INSERT INTO _LNResearch_NodeAddresses
                        (NodeID, Address, Port, FirstSeen, LastSeen) VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        FirstSeen = LEAST(FirstSeen, VALUES(FirstSeen)),
                        LastSeen = GREATEST(LastSeen, VALUES(LastSeen))
                ''', [node_id, nodeAddress, nodePort, timestamp, timestamp])
                addressID += 1



        # Channel Update (not used for now)
        elif msg_type == 258:
            pass
            # signature = msg[2:66].hex()
            # chain_hash = msg[66:98].hex()
            # short_channel_id = int.from_bytes(msg[98:106], byteorder='big')
            # timestamp = int.from_bytes(msg[106:110], byteorder='big')
            # message_flags = msg[110]
            # channel_flags = msg[111]
            # cltv_expiry_delta = int.from_bytes(msg[112:114], byteorder='big')
            # htlc_minimum_msat = int.from_bytes(msg[114:122], byteorder='big')
            # fee_base_msat = int.from_bytes(msg[122:126], byteorder='big')
            # fee_proportional_millionths = int.from_bytes(msg[126:130], byteorder='big')

            # db_cursor.execute(f'''
            #     INSERT IGNORE INTO _LNResearch_ChannelUpdates (
            #         signature, chain_hash, short_channel_id, timestamp, message_flags,
            #         channel_flags, cltv_expiry_delta, htlc_minimum_msat, fee_base_msat,
            #         fee_proportional_millionths
            #     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # ''', [
            #     signature,
            #     chain_hash,
            #     short_channel_id,
            #     timestamp,
            #     message_flags,
            #     channel_flags,
            #     cltv_expiry_delta,
            #     htlc_minimum_msat,
            #     fee_base_msat,
            #     fee_proportional_millionths
            # ])



        else:
            print(f"Unknown message type: {msg_type}")
            return ''



    def __parse_addresses(self, data):
        i = 0
        addresses = []
        while i < len(data):
            addr_type = data[i]
            i += 1
            if addr_type == 1:  # IPv4
                ip = ".".join(map(str, data[i:i+4]))
                port = int.from_bytes(data[i+4:i+6], byteorder='big')
                addresses.append((ip, port))
                i += 6
            elif addr_type == 2:  # IPv6
                ip = ":".join(["%x" % int.from_bytes(data[i+j:i+j+2], byteorder='big') for j in range(0, 16, 2)])
                port = int.from_bytes(data[i+16:i+18], byteorder='big')
                addresses.append((ip, port))
                i += 18
            elif addr_type == 3:  # Tor v2
                ip = data[i:i+10].hex()
                port = int.from_bytes(data[i+10:i+12], byteorder='big')
                addresses.append((ip, port))
                i += 12
            elif addr_type == 4:  # Tor v3
                ip = data[i:i+35].hex()
                port = int.from_bytes(data[i+35:i+37], byteorder='big')
                addresses.append((ip, port))
                i += 37
            else:
                # Unknown address type, skip the rest of the data for safety
                break
        return addresses



    def __hex_to_onion(self, hex_str):
        decoded_bytes = bytes.fromhex(hex_str)
        encoded_base32 = base64.b32encode(decoded_bytes).decode('utf-8').lower().rstrip('=')
        return f"{encoded_base32}.onion"



    def __create_tables_if_not_exists(self):
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `_LNResearch_ChannelAnnouncements` (
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
                    CREATE TABLE IF NOT EXISTS `_LNResearch_NodeAnnouncements` ( 
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
                    CREATE TABLE IF NOT EXISTS `_LNResearch_NodeAddresses` ( 
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

                # # Channel updates are not used for now
                # cursor.execute(f'''
                #     CREATE TABLE IF NOT EXISTS `_LNResearch_ChannelUpdates` (
                #         `signature` CHAR(128) NOT NULL,
                #         `chain_hash` CHAR(64) NOT NULL,
                #         `short_channel_id` BIGINT NOT NULL,
                #         `timestamp` INT NOT NULL,
                #         `message_flags` TINYINT UNSIGNED NOT NULL,
                #         `channel_flags` TINYINT UNSIGNED NOT NULL,
                #         `cltv_expiry_delta` SMALLINT UNSIGNED NOT NULL,
                #         `htlc_minimum_msat` BIGINT UNSIGNED NOT NULL,
                #         `fee_base_msat` INT UNSIGNED NOT NULL,
                #         `fee_proportional_millionths` INT UNSIGNED NOT NULL,
                #         UNIQUE KEY (`short_channel_id`, `timestamp`, `channel_flags`),
                #         INDEX idx_timestamp (`timestamp`),
                #         INDEX idx_channel_flags_short_channel_id (`channel_flags`, `short_channel_id`)
                #     );
                # ''')



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
                    FROM _LNResearch_ChannelAnnouncements ca
                ''')
                conn.commit()



    def __import_data(self, filename: str):
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                with bz2.open(filename, 'rb') as f:
                    header = f.read(4)
                    assert(header[:3] == b'GSP' and header[3] == 1)

                    insertedMessageCounter = 0
                    while True:
                        length = varint_decode(f)
                        msg = f.read(length)

                        if(length == None):
                            break
                        
                        if len(msg) != length:
                            continue

                        self.__parse_message(db_cursor, msg)
                        
                        # Commit only every 10000 rows
                        insertedMessageCounter += 1
                        if(insertedMessageCounter % 10000 == 0):
                            db_conn.commit()

                    # Commit any remaining uncommitted rows after the loop
                    db_conn.commit()



