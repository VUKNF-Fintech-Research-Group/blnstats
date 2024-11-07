import socket
import json
import hashlib
from decimal import Decimal
from multiprocessing import Pool
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from ..database.utils import get_db_connection



class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)




class BlockchainTransactions:
    """
    Class for importing blockchain transaction data into the database.

    This class is designed to handle the retrieval and storage of blockchain transaction data,
    specifically focusing on the funding and spending of Lightning Network channels.
    """

    def __init__(self, btc_rpc_user: str, btc_rpc_password: str, btc_rpc_ip: str, btc_rpc_port: int, electrum_host: str, electrum_port: int):
        """
        Initializes the BlockchainTransactions class with Bitcoin RPC and Electrum server credentials.

        :param btc_rpc_user: str - Bitcoin RPC username.
        :param btc_rpc_password: str - Bitcoin RPC password.
        :param btc_rpc_ip: str - Bitcoin RPC IP address.
        :param btc_rpc_port: int - Bitcoin RPC port.
        :param electrum_host: str - Electrum server IP address.
        :param electrum_port: int - Electrum server port. 
        """
        self.btc_rpc_user = btc_rpc_user
        self.btc_rpc_password = btc_rpc_password
        self.btc_rpc_ip = btc_rpc_ip
        self.btc_rpc_port = btc_rpc_port
        self.electrum_host = electrum_host
        self.electrum_port = electrum_port

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                self.__createTablesIfNotExist(db_cursor)




    def __createTablesIfNotExist(self, db_cursor):
        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS `Blockchain_Transactions` (
                `ShortChannelID` BIGINT UNSIGNED NOT NULL UNIQUE,
                `FundingBlockIndex` INT UNSIGNED NOT NULL,
                `FundingTxIndex` INT UNSIGNED NOT NULL,
                `FundingOutputIndex` SMALLINT UNSIGNED NOT NULL,
                `FundingTxID` CHAR(64) NOT NULL,
                `FundingScriptHash` CHAR(64) NOT NULL,
                `Value` BIGINT UNSIGNED NOT NULL,
                `SpendingBlockIndex` INT UNSIGNED NOT NULL,
                `SpendingTxID` CHAR(64) NOT NULL,
                PRIMARY KEY (`ShortChannelID`),
                INDEX `idx_Funding_SpendingBlockIndex` (`FundingBlockIndex`, `SpendingBlockIndex`),
                INDEX `idx_Value` (`Value`)
            );
        ''')



    def __send_electrum_request(self, server_ip: str, server_port: int, method: str, params: list):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, server_port))

        request = {
            "id": 0,
            "method": method,
            "params": params
        }
        request_str = json.dumps(request) + '\n'
        s.sendall(request_str.encode())

        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b'\n' in chunk:
                break
        s.close()

        response = b''.join(chunks).decode()
        response_json = json.loads(response)
        
        if 'error' in response_json and response_json['error']:
            print(f"Error from Electrum server: {response_json['error']['message']}")
            return None

        return response_json.get('result')


    def __get_transaction_details(self, block_height: int, tx_index: int, output_index: int):
        try:
            rpc_connection = AuthServiceProxy(f"http://{self.btc_rpc_user}:{self.btc_rpc_password}@{self.btc_rpc_ip}:{self.btc_rpc_port}")

            block_hash = rpc_connection.getblockhash(block_height)
            block = rpc_connection.getblock(block_hash)
            tx_id = block['tx'][tx_index]
            tx_details = rpc_connection.getrawtransaction(tx_id, 1)
            output_details = tx_details['vout'][output_index]

            return tx_id, output_details

        except JSONRPCException as json_exception:
            print(f"An error occurred: {json_exception}")
            return None, None


    def __get_script_hash_from_output(self, output_details):
        script_pub_key = output_details['scriptPubKey']['hex']
        script_pub_key_bytes = bytes.fromhex(script_pub_key)
        sha256_hash = hashlib.sha256(script_pub_key_bytes).digest()
        reversed_hash = sha256_hash[::-1]
        script_hash = reversed_hash.hex()
        return script_hash


    def __get_spending_time_for_output(self, tx_id_to_check, output_index_to_check, script_hash_history):
        for entry in script_hash_history:
            tx_hash = entry['tx_hash']
            tx_details = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.transaction.get", [tx_hash, True])
            
            for vin in tx_details['vin']:
                if vin['txid'] == tx_id_to_check and vin['vout'] == output_index_to_check:
                    return entry['height'], tx_hash
        return None, None


    def retrieveAndWriteLightningBlockchainTxData(self, data):
        blockIndex, txIndex, outputIndex, shortChannelID = data

        print(f"{blockIndex}:{txIndex}:{outputIndex}")

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                tx_id, output_details = self.__get_transaction_details(blockIndex, txIndex, outputIndex)
                if output_details:
                    output_details = json.loads(json.dumps(output_details, indent=4, cls=DecimalEncoder))
                    tx_output_value_btc = Decimal(str(output_details['value']))
                    tx_output_value_satoshis = int(tx_output_value_btc * Decimal('100000000'))


                    funding_script_hash = self.__get_script_hash_from_output(output_details)
                    funding_script_hash_history = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.scripthash.get_history", [funding_script_hash])

                    spending_block_height, spending_tx_id = self.__get_spending_time_for_output(tx_id, outputIndex, funding_script_hash_history)

                    db_cursor.execute(f'''
                        REPLACE INTO Blockchain_Transactions (
                            ShortChannelID, FundingBlockIndex, FundingTxIndex, FundingOutputIndex,
                            FundingTxID, FundingScriptHash, Value, SpendingBlockIndex, SpendingTxID
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', [
                        shortChannelID,
                        blockIndex,
                        txIndex,
                        outputIndex,
                        tx_id,
                        funding_script_hash,
                        tx_output_value_satoshis,
                        spending_block_height or '999999999',
                        spending_tx_id or ''
                    ])
                    db_conn.commit()


    def run(self, blockRange):
        stepSize = 100
        for fromBlock in range(blockRange * stepSize, 999999, stepSize):
            toBlock = fromBlock + stepSize
            
            
            with get_db_connection() as db_conn:
                with db_conn.cursor() as db_cursor:
                    # Use %s placeholders and pass parameters as a tuple
                    db_cursor.execute(''' 
                        SELECT
                            blockchain_height,
                            blockchain_tx_index, 
                            blockchain_output_index,
                            short_channel_id
                        FROM 
                            LNResearch_20230924_ChannelAnnouncement
                        WHERE blockchain_height >= %s AND blockchain_height < %s
                            AND short_channel_id NOT IN (SELECT ShortChannelID FROM Blockchain_Transactions)
                        ORDER BY 
                            blockchain_height, blockchain_tx_index
                    ''', [fromBlock, toBlock])

                    # Fetch all results after executing the query
                    sqlFetchData = db_cursor.fetchall()

                    toCheck = []
                    for sqlLine in sqlFetchData:
                        blockIndex, txIndex, outputIndex, shortChannelID = sqlLine
                        toCheck.append([blockIndex, txIndex, outputIndex, shortChannelID])

                    while True:
                        try:
                            with Pool(processes=15) as pool:
                                pool.map(self.retrieveAndWriteLightningBlockchainTxData, toCheck)
                        except Exception as e:
                            print(e)
                            continue
                        break




