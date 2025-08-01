import bz2
from pyln.proto.primitives import varint_decode
from pyln.proto.message import Message
import base64
from ..database.utils import get_db_connection



class LNResearchData:
    """
    Class for importing LN Research dataset into the database.

    This class is designed to handle the parsing and storage of LN Research dataset files,
    which contain data related to the Lightning Network such as channel announcements,
    node announcements, and channel updates.

    Usage:
    ```python
    LNResearchData(file_path)
    ```
    """

    def __init__(self, file_path: str):
        """
        Initializes the LNResearchData class with the path to the LN Research dataset file.

        :param file_path: str - Path to the LN Research dataset file.
        """
        print(f"[*] Importing LN Research dataset from '{file_path}'")
        self.__read_dataset(file_path)



    def __parse_message(self, db_conn, db_cursor, lnresearch_version, msg: bytes):
        # Extract the message type from the first two bytes
        msg_type = int.from_bytes(msg[:2], byteorder='big')

        # channel_announcement
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

            # Use %s placeholders and INSERT IGNORE for MySQL
            db_cursor.execute(f'''
                INSERT IGNORE INTO _LNResearch_{lnresearch_version}_ChannelAnnouncement (
                    features_len, features, chain_hash, short_channel_id, blockchain_height,
                    blockchain_tx_index, blockchain_output_index, node_id_1, node_id_2,
                    bitcoin_key_1, bitcoin_key_2
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', [
                features_len,
                features,
                chain_hash,
                short_channel_id,
                block_height,
                tx_index,
                output_index,
                node_id_1,
                node_id_2,
                bitcoin_key_1,
                bitcoin_key_2
            ])



        # node_announcement
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
            print(parsed_addresses)

            db_cursor.execute(f'''
                INSERT INTO _LNResearch_{lnresearch_version}_NodeAnnouncement (
                    signature, features_len, features, timestamp, node_id, rgb_color, alias, addresses
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', [
                signature,
                features_len,
                features,
                timestamp,
                node_id,
                rgb_color,
                alias,
                addresses
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

                # Use REPLACE INTO for MySQL
                db_cursor.execute(f'''
                    REPLACE INTO _LNResearch_{lnresearch_version}_NodeAddresses (
                        NodeID, AddressID, AddressType, Address, Port
                    ) VALUES (%s, %s, %s, %s, %s)
                ''', [node_id, addressID, addressType, nodeAddress, nodePort])
                addressID += 1



        # channel_update
        elif msg_type == 258:
            signature = msg[2:66].hex()
            chain_hash = msg[66:98].hex()
            short_channel_id = int.from_bytes(msg[98:106], byteorder='big')
            timestamp = int.from_bytes(msg[106:110], byteorder='big')
            message_flags = msg[110]
            channel_flags = msg[111]
            cltv_expiry_delta = int.from_bytes(msg[112:114], byteorder='big')
            htlc_minimum_msat = int.from_bytes(msg[114:122], byteorder='big')
            fee_base_msat = int.from_bytes(msg[122:126], byteorder='big')
            fee_proportional_millionths = int.from_bytes(msg[126:130], byteorder='big')

            db_cursor.execute(f'''
                INSERT IGNORE INTO _LNResearch_{lnresearch_version}_ChannelUpdate (
                    signature, chain_hash, short_channel_id, timestamp, message_flags,
                    channel_flags, cltv_expiry_delta, htlc_minimum_msat, fee_base_msat,
                    fee_proportional_millionths
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', [
                signature,
                chain_hash,
                short_channel_id,
                timestamp,
                message_flags,
                channel_flags,
                cltv_expiry_delta,
                htlc_minimum_msat,
                fee_base_msat,
                fee_proportional_millionths
            ])



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



    def __createTablesIfNotExist(self, db_cursor, lnresearch_version):
        db_cursor.execute(f''' 
            CREATE TABLE IF NOT EXISTS `_LNResearch_{lnresearch_version}_ChannelAnnouncement` (
                `features_len` INT NOT NULL,
                `features` TEXT NOT NULL,
                `chain_hash` CHAR(64) NOT NULL,
                `short_channel_id` BIGINT NOT NULL,
                `blockchain_height` INT NOT NULL,
                `blockchain_tx_index` INT NOT NULL,
                `blockchain_output_index` INT NOT NULL,
                `node_id_1` CHAR(66) NOT NULL,
                `node_id_2` CHAR(66) NOT NULL,
                `bitcoin_key_1` CHAR(66) NOT NULL,
                `bitcoin_key_2` CHAR(66) NOT NULL,
                PRIMARY KEY (`short_channel_id`),
                INDEX idx_blockchain_height (`blockchain_height`),
                INDEX idx_node_id_1 (`node_id_1`),
                INDEX idx_node_id_2 (`node_id_2`)
            );
        ''')

        db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS `_LNResearch_{lnresearch_version}_NodeAnnouncement` (
                `signature` CHAR(128) NOT NULL,
                `features_len` INT NOT NULL,
                `features` TEXT NOT NULL,
                `timestamp` INT NOT NULL,
                `node_id` CHAR(66) NOT NULL,
                `rgb_color` CHAR(6) NOT NULL,
                `alias` VARCHAR(32) NOT NULL,
                `addresses` TEXT NOT NULL,
                UNIQUE KEY (`node_id`, `timestamp`),
                INDEX idx_timestamp (`timestamp`),
                INDEX idx_alias (`alias`)
            );
        ''')

        db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS `_LNResearch_{lnresearch_version}_NodeAddresses` (
                `NodeID` CHAR(66) NOT NULL,
                `AddressID` INT NOT NULL,
                `AddressType` VARCHAR(16) NOT NULL,
                `Address` VARCHAR(255) NOT NULL,
                `Port` INT NOT NULL,
                UNIQUE KEY (`NodeID`, `Address`),
                INDEX idx_NodeID (`NodeID`),
                INDEX idx_AddressType (`AddressType`)
            );
        ''')

        db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS `_LNResearch_{lnresearch_version}_ChannelUpdate` (
                `signature` CHAR(128) NOT NULL,
                `chain_hash` CHAR(64) NOT NULL,
                `short_channel_id` BIGINT NOT NULL,
                `timestamp` INT NOT NULL,
                `message_flags` TINYINT UNSIGNED NOT NULL,
                `channel_flags` TINYINT UNSIGNED NOT NULL,
                `cltv_expiry_delta` SMALLINT UNSIGNED NOT NULL,
                `htlc_minimum_msat` BIGINT UNSIGNED NOT NULL,
                `fee_base_msat` INT UNSIGNED NOT NULL,
                `fee_proportional_millionths` INT UNSIGNED NOT NULL,
                UNIQUE KEY (`short_channel_id`, `timestamp`, `channel_flags`),
                INDEX idx_timestamp (`timestamp`),
                INDEX idx_channel_flags_short_channel_id (`channel_flags`, `short_channel_id`)
            );
        ''')

        # db_cursor.execute(f'''
        #     CREATE TABLE IF NOT EXISTS `IPGeolocation` (
        #         `Address` VARCHAR(255) NOT NULL UNIQUE,
        #         `CountryCode` VARCHAR(10) NOT NULL,
        #         UNIQUE(`Address`, `CountryCode`)
        #     );
        # ''')


    def push_data_to_main_tables():
        '''
        INSERT INTO Lightning_Channels
        SELECT
            _LNResearch_20230924_ChannelAnnouncement.short_channel_id,
            _LNResearch_20230924_ChannelAnnouncement.blockchain_height,
            _LNResearch_20230924_ChannelAnnouncement.blockchain_tx_index,
            _LNResearch_20230924_ChannelAnnouncement.blockchain_output_index,
            _LNResearch_20230924_ChannelAnnouncement.node_id_1,
            _LNResearch_20230924_ChannelAnnouncement.node_id_2
        FROM _LNResearch_20230924_ChannelAnnouncement
        '''



    def __read_dataset(self, filename: str):
        timeframe = filename.split("-")[1].split(".")[0]

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                self.__createTablesIfNotExist(db_cursor, timeframe)

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

                        self.__parse_message(db_conn, db_cursor, timeframe, msg)
                        
                        # Commit only every 10000 rows
                        insertedMessageCounter += 1
                        if(insertedMessageCounter % 10000 == 0):
                            db_conn.commit()

                    # Commit any remaining uncommitted rows after the loop
                    db_conn.commit()



