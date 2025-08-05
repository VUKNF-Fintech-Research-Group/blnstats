import socket
import json
import hashlib
import time
import logging
from decimal import Decimal
from multiprocessing.dummy import Pool as ThreadPool
from ..database.utils import get_db_connection
from dataclasses import dataclass
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug flag to control verbose output
DEBUG_ENABLED = False


class TransactionSyncError(Exception):
    """Exception raised when transactions fail to sync after all retry attempts."""
    
    def __init__(self, failed_transactions: Dict[Tuple[int, int, int, int], str], total_transactions_attempted: int):
        self.failed_transactions = failed_transactions
        self.total_transactions_attempted = total_transactions_attempted
        self.failed_count = len(failed_transactions)
        
        message = (f"Failed to sync {self.failed_count} out of {total_transactions_attempted} transactions. "
                  f"Failed transactions: {list(failed_transactions.keys())}")
        super().__init__(message)


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

    def __init__(self, electrum_host: str, electrum_port: int):
        """
        Initializes the BlockchainTransactions class with Electrum server credentials.

        :param electrum_host: str - Electrum server IP address.
        :param electrum_port: int - Electrum server port. 
        """
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
                `UpdatedDate` DATE NOT NULL,
                PRIMARY KEY (`ShortChannelID`),
                INDEX `idx_Funding_SpendingBlockIndex` (`FundingBlockIndex`, `SpendingBlockIndex`),
                INDEX `idx_Value` (`Value`)
            );
        ''')



    def __send_electrum_request(self, server_ip: str, server_port: int, method: str, params: list):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
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


            # Construct response and parse as JSON
            response = b''.join(chunks).decode()
            response_json = json.loads(response)

            
            # Safely check for errors
            if isinstance(response_json, dict) and 'error' in response_json and response_json['error']:
                error_info = response_json['error']
                if isinstance(error_info, dict) and 'message' in error_info:
                    logger.error(f"Error from Electrum server for method {method}: {error_info['message']}")
                else:
                    logger.error(f"Error from Electrum server for method {method}: {error_info}")
                return None

            return response_json.get('result') if isinstance(response_json, dict) else response_json
            
        except Exception as e:
            logger.error(f"Network error calling Electrum method {method}: {e}")
            return None



    def __parse_raw_transaction(self, raw_tx_hex: str, output_index: int):
        """
        Parse a raw Bitcoin transaction hex string to extract output details.
        Handles both legacy and SegWit transaction formats.
        """
        try:
            if DEBUG_ENABLED:
                print(f"DEBUG: Parsing transaction hex (length: {len(raw_tx_hex)}) for output index {output_index}")
            
            # Convert hex string to bytes
            tx_bytes = bytes.fromhex(raw_tx_hex)
            offset = 0
            
            # Read version (4 bytes)
            version = int.from_bytes(tx_bytes[offset:offset + 4], 'little')
            if DEBUG_ENABLED:
                print(f"DEBUG: Transaction version: {version}")
            offset += 4
            
            # Check for SegWit transaction (marker = 0x00, flag = 0x01)
            is_segwit = False
            if tx_bytes[offset] == 0x00 and tx_bytes[offset + 1] == 0x01:
                if DEBUG_ENABLED:
                    print("DEBUG: SegWit transaction detected")
                is_segwit = True
                offset += 2  # Skip marker and flag
            
            # Read input count
            input_count, offset = self.__read_varint(tx_bytes, offset)
            if DEBUG_ENABLED:
                print(f"DEBUG: Input count: {input_count}")
            
            # Skip all inputs
            for i in range(input_count):
                if DEBUG_ENABLED:
                    print(f"DEBUG: Processing input {i}")
                # Skip previous output hash (32 bytes)
                offset += 32
                # Skip previous output index (4 bytes)
                offset += 4
                # Read script length and skip script
                script_length, offset = self.__read_varint(tx_bytes, offset)
                if DEBUG_ENABLED:
                    print(f"DEBUG: Input {i} script length: {script_length}")
                offset += script_length
                # Skip sequence (4 bytes)
                offset += 4
            
            # Read output count
            output_count, offset = self.__read_varint(tx_bytes, offset)
            if DEBUG_ENABLED:
                print(f"DEBUG: Output count: {output_count}, requested index: {output_index}")
            
            if output_index >= output_count:
                print(f"ERROR: Output index {output_index} out of range (transaction has {output_count} outputs)")
                return None
            
            # Skip to the desired output
            for i in range(output_index):
                if DEBUG_ENABLED:
                    print(f"DEBUG: Skipping output {i}")
                # Skip value (8 bytes)
                offset += 8
                # Read script length and skip script
                script_length, offset = self.__read_varint(tx_bytes, offset)
                if DEBUG_ENABLED:
                    print(f"DEBUG: Output {i} script length: {script_length}")
                offset += script_length
            
            if DEBUG_ENABLED:
                print(f"DEBUG: Reading target output {output_index} at offset {offset}")
            
            # Read the target output
            # Read value (8 bytes, little endian)
            value_bytes = tx_bytes[offset:offset + 8]
            value_satoshis = int.from_bytes(value_bytes, 'little')
            if DEBUG_ENABLED:
                print(f"DEBUG: Output value: {value_satoshis} satoshis")
            offset += 8
            
            # Read script
            script_length, offset = self.__read_varint(tx_bytes, offset)
            if DEBUG_ENABLED:
                print(f"DEBUG: Target output script length: {script_length}")
            script_bytes = tx_bytes[offset:offset + script_length]
            script_hex = script_bytes.hex()
            if DEBUG_ENABLED:
                print(f"DEBUG: Script hex: {script_hex}")
            
            # Note: We're not parsing witness data since we only need output information
            
            return {
                'value': value_satoshis / 100000000,  # Convert to BTC
                'scriptPubKey': {'hex': script_hex}
            }
            
        except Exception as e:
            print(f"Error parsing raw transaction: {e}")
            if DEBUG_ENABLED:
                import traceback
                traceback.print_exc()
            return None



    def __read_varint(self, data: bytes, offset: int):
        """
        Read a variable length integer from Bitcoin transaction data.
        Returns (value, new_offset)
        """
        first_byte = data[offset]
        
        if first_byte < 0xfd:
            return first_byte, offset + 1
        elif first_byte == 0xfd:
            return int.from_bytes(data[offset + 1:offset + 3], 'little'), offset + 3
        elif first_byte == 0xfe:
            return int.from_bytes(data[offset + 1:offset + 5], 'little'), offset + 5
        elif first_byte == 0xff:
            return int.from_bytes(data[offset + 1:offset + 9], 'little'), offset + 9



    def __get_transaction_details(self, block_height: int, tx_index: int, output_index: int):
        try:
            tx_id_raw = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.transaction.id_from_pos", [block_height, tx_index])
            
            if not tx_id_raw:
                return None, None

            # Handle case where tx_id might be returned as JSON string
            tx_id = tx_id_raw
            while isinstance(tx_id, str) and tx_id.startswith('"') and tx_id.endswith('"'):
                tx_id = json.loads(tx_id)

            # Get the raw transaction hex
            raw_tx_hex = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.transaction.get", [tx_id])
            
            if not raw_tx_hex:
                return None, None

            # Parse the raw transaction to get output details
            output_details = self.__parse_raw_transaction(raw_tx_hex, output_index)
            
            if not output_details:
                print(f"Failed to parse transaction {tx_id} at block {block_height}, tx {tx_index}, output {output_index}")
                return None, None

            return tx_id, output_details

        except Exception as e:
            print(f"An error occurred in __get_transaction_details: {e}")
            return None, None



    def __get_script_hash_from_output(self, output_details):
        """
        This function converts a scriptPubKey to a script hash.
        It does this by hashing the scriptPubKey and reversing the hash.
        The script hash is used to identify the output in the blockchain.
        """
        script_pub_key = output_details['scriptPubKey']['hex']
        script_pub_key_bytes = bytes.fromhex(script_pub_key)
        sha256_hash = hashlib.sha256(script_pub_key_bytes).digest()
        reversed_hash = sha256_hash[::-1]
        script_hash = reversed_hash.hex()
        return script_hash



    def __get_spending_time_for_output(self, tx_id_to_check, output_index_to_check, script_hash_history):
        """
        This function checks if a specific output (txid:vout) has been spent in a transaction.
        It does this by checking the script hash history of the output.
        If the output has been spent, it returns the block height and transaction ID of the spending transaction.
        If the output has not been spent, it returns None.

        :param tx_id_to_check: str - The transaction ID of the output to check.
        :param output_index_to_check: int - The index of the output to check.
        :return: Tuple (block_height, tx_id) or (None, None) if not spent, or raises exception on network errors
        """
        if DEBUG_ENABLED:
            logger.debug(f"Checking spending for {tx_id_to_check}:{output_index_to_check}")
            logger.debug(f"Script hash history has {len(script_hash_history) if script_hash_history else 0} entries")
        
        network_errors = 0
        max_network_errors = 3  # Allow some network errors but not too many
        
        for entry in script_hash_history:
            tx_hash = entry['tx_hash']
            
            if DEBUG_ENABLED:
                logger.debug(f"Checking transaction {tx_hash} at height {entry['height']}")
            
            # Get raw transaction hex (not verbose since Electrum doesn't support it)
            raw_tx_hex = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.transaction.get", [tx_hash])
            
            if not raw_tx_hex:
                network_errors += 1
                logger.warning(f"Could not get raw hex for {tx_hash} (error {network_errors}/{max_network_errors})")
                
                if network_errors >= max_network_errors:
                    raise Exception(f"Too many network errors ({network_errors}) while checking spending transactions")
                continue
                
            # Parse the raw transaction to check if it spends our output
            if self.__transaction_spends_output(raw_tx_hex, tx_id_to_check, output_index_to_check):
                if DEBUG_ENABLED:
                    logger.debug("Found spending transaction!")
                return entry['height'], tx_hash
        
        if DEBUG_ENABLED:
            logger.debug("No spending transaction found")
        return None, None



    def __transaction_spends_output(self, raw_tx_hex: str, target_txid: str, target_output_index: int):
        """
        Check if a raw transaction spends a specific output (txid:vout).
        Returns True if the transaction spends the target output.
        """
        try:
            tx_bytes = bytes.fromhex(raw_tx_hex)
            offset = 0
            
            # Skip version (4 bytes)
            offset += 4
            
            # Check for SegWit transaction (marker = 0x00, flag = 0x01)
            if tx_bytes[offset] == 0x00 and tx_bytes[offset + 1] == 0x01:
                offset += 2  # Skip marker and flag
            
            # Read input count
            input_count, offset = self.__read_varint(tx_bytes, offset)
            
            if DEBUG_ENABLED:
                print(f"DEBUG: Checking {input_count} inputs in spending candidate")
            
            # Check each input
            for i in range(input_count):
                # Read previous output hash (32 bytes)
                prev_hash_bytes = tx_bytes[offset:offset + 32]
                prev_hash = prev_hash_bytes[::-1].hex()  # Reverse for little-endian to big-endian
                offset += 32
                
                # Read previous output index (4 bytes, little endian)
                prev_index_bytes = tx_bytes[offset:offset + 4]
                prev_index = int.from_bytes(prev_index_bytes, 'little')
                offset += 4
                
                if DEBUG_ENABLED:
                    print(f"DEBUG: Input {i}: {prev_hash}:{prev_index}")
                    print(f"DEBUG: Target: {target_txid}:{target_output_index}")
                
                # Check if this input spends our target output
                if prev_hash == target_txid and prev_index == target_output_index:
                    if DEBUG_ENABLED:
                        print(f"DEBUG: MATCH FOUND!")
                    return True
                
                # Skip script length and script
                script_length, offset = self.__read_varint(tx_bytes, offset)
                offset += script_length
                
                # Skip sequence (4 bytes)
                offset += 4
            
            return False
            
        except Exception as e:
            print(f"Error checking if transaction spends output: {e}")
            return False



    def retrieveAndWriteLightningBlockchainTxData(self, data):
        """
        This function retrieves the transaction details for a specific output and writes them to the database.
        It does this by checking the script hash history of the output.
        If the output has been spent, it returns the block height and transaction ID of the spending transaction.
        
        :param data: List containing [blockIndex, txIndex, outputIndex, shortChannelID]
        :return: Tuple of (transaction_info, success_status, error_message)
        """
        blockIndex, txIndex, outputIndex, shortChannelID = data
        transaction_info = (blockIndex, txIndex, outputIndex, shortChannelID)

        try:
            logger.info(f"Processing transaction {blockIndex}:{txIndex}:{outputIndex}")

            with get_db_connection() as db_conn:
                with db_conn.cursor() as db_cursor:
                    tx_id, output_details = self.__get_transaction_details(blockIndex, txIndex, outputIndex)
                    if not output_details:
                        error_msg = f"Could not retrieve transaction details for {blockIndex}:{txIndex}:{outputIndex}"
                        logger.error(error_msg)
                        return (transaction_info, False, error_msg)

                    output_details = json.loads(json.dumps(output_details, indent=4, cls=DecimalEncoder))
                    tx_output_value_btc = Decimal(str(output_details['value']))
                    tx_output_value_satoshis = int(tx_output_value_btc * Decimal('100000000'))

                    funding_script_hash = self.__get_script_hash_from_output(output_details)
                    funding_script_hash_history = self.__send_electrum_request(self.electrum_host, self.electrum_port, "blockchain.scripthash.get_history", [funding_script_hash])

                    if funding_script_hash_history is None:
                        error_msg = f"Could not retrieve script hash history for {blockIndex}:{txIndex}:{outputIndex}"
                        logger.error(error_msg)
                        return (transaction_info, False, error_msg)

                    spending_block_height, spending_tx_id = self.__get_spending_time_for_output(tx_id, outputIndex, funding_script_hash_history)

                    # Print status based on whether the output has been spent
                    if spending_block_height and spending_tx_id:
                        logger.info(f"Transaction {blockIndex}:{txIndex}:{outputIndex} ({shortChannelID}) -> SPENT in block {spending_block_height}, tx {spending_tx_id}")

                    db_cursor.execute('''
                        INSERT INTO Blockchain_Transactions (
                            ShortChannelID, FundingBlockIndex, FundingTxIndex, FundingOutputIndex,
                            FundingTxID, FundingScriptHash, Value, SpendingBlockIndex, SpendingTxID, UpdatedDate
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
                        ON DUPLICATE KEY UPDATE
                            FundingBlockIndex = VALUES(FundingBlockIndex),
                            FundingTxIndex = VALUES(FundingTxIndex),
                            FundingOutputIndex = VALUES(FundingOutputIndex),
                            FundingTxID = VALUES(FundingTxID),
                            FundingScriptHash = VALUES(FundingScriptHash),
                            Value = VALUES(Value),
                            SpendingBlockIndex = VALUES(SpendingBlockIndex),
                            SpendingTxID = VALUES(SpendingTxID),
                            UpdatedDate = CURDATE()
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

            logger.info(f"Transaction {blockIndex}:{txIndex}:{outputIndex} processed successfully")
            return (transaction_info, True, None)

        except Exception as e:
            error_msg = f"Error processing transaction {blockIndex}:{txIndex}:{outputIndex}: {str(e)}"
            logger.error(error_msg)
            return (transaction_info, False, error_msg)



    def run(self, blockRange):
        """
        Process Lightning Network transactions for a given block range.
        
        :param blockRange: Starting block range multiplier
        :raises TransactionSyncError: If any transactions fail to sync after all retry attempts
        """
        stepSize = 1000
        max_retries = 10  # Maximum number of retries for failed transactions
        retry_delay = 15  # Delay in seconds before retrying failed transactions
        
        # Track overall sync results
        all_failed_transactions = {}  # (blockIndex, txIndex, outputIndex, shortChannelID) -> error_message
        total_transactions_attempted = 0
        

        # Get the highest block in the Lightning_Channels
        highestChannelBlock = 0
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                db_cursor.execute(' SELECT MAX(BlockIndex) FROM Lightning_Channels ')
                highestChannelBlock = db_cursor.fetchone()[0] + stepSize


        # Process transactions
        for fromBlock in range(blockRange * stepSize, highestChannelBlock, stepSize):
            toBlock = fromBlock + stepSize
            
            with get_db_connection() as db_conn:
                with db_conn.cursor() as db_cursor:
                    db_cursor.execute('''
                        SELECT
                            BlockIndex,
                            TxIndex, 
                            OutputIndex,
                            ShortChannelID
                        FROM 
                            Lightning_Channels
                        WHERE 
                            BlockIndex >= %s AND BlockIndex < %s
                            AND ShortChannelID NOT IN (
                                SELECT ShortChannelID 
                                FROM Blockchain_Transactions 
                                WHERE SpendingBlockIndex <> 999999999 
                                   OR UpdatedDate >= CURDATE() - INTERVAL 7 DAY
                            )
                        ORDER BY 
                            BlockIndex, TxIndex
                    ''', [fromBlock, toBlock])

                    # Fetch all results after executing the query
                    sqlFetchData = db_cursor.fetchall()

                    toCheck = []
                    for sqlLine in sqlFetchData:
                        blockIndex, txIndex, outputIndex, shortChannelID = sqlLine
                        toCheck.append([blockIndex, txIndex, outputIndex, shortChannelID])

                    if not toCheck:
                        logger.info(f"No transactions to process in range {fromBlock} to {toBlock}")
                        continue

                    logger.info(f"Processing {len(toCheck)} transactions from {fromBlock} to {toBlock}")
                    total_transactions_attempted += len(toCheck)

                    # Track failed transactions for retry
                    transactions_to_process = toCheck
                    retry_count = 0
                    
                    while transactions_to_process and retry_count < max_retries:
                        try:
                            with ThreadPool(10) as pool:
                                results = pool.map(self.retrieveAndWriteLightningBlockchainTxData, transactions_to_process)
                            
                            # Process results and identify failed transactions
                            successful_transactions = []
                            failed_transactions = []
                            
                            for transaction_info, success, error_msg in results:
                                if success:
                                    successful_transactions.append(transaction_info)
                                else:
                                    failed_transactions.append((transaction_info, error_msg))
                            
                            logger.info(f"Batch {fromBlock}-{toBlock}: {len(successful_transactions)} successful, {len(failed_transactions)} failed")
                            
                            if failed_transactions:
                                logger.warning(f"Failed transactions in retry {retry_count + 1}: {[t[0] for t, _ in failed_transactions]}")
                                if retry_count < max_retries - 1:
                                    transactions_to_process = [[t[0], t[1], t[2], t[3]] for (t, _) in failed_transactions]
                                    logger.info(f"Waiting {retry_delay} seconds before retrying {len(transactions_to_process)} failed transactions...")
                                    time.sleep(retry_delay)
                                else:
                                    # Log permanently failed transactions and add to overall tracking
                                    for transaction_info, error_msg in failed_transactions:
                                        logger.error(f"Transaction {transaction_info} permanently failed after {max_retries} attempts: {error_msg}")
                                        all_failed_transactions[transaction_info] = error_msg
                            else:
                                transactions_to_process = []  # All transactions successful
                                
                        except Exception as e:
                            logger.error(f"Pool error processing transactions {fromBlock} to {toBlock} (attempt {retry_count + 1}): {e}")
                            if retry_count < max_retries - 1:
                                logger.info(f"Waiting {retry_delay} seconds before retrying due to pool error...")
                                time.sleep(retry_delay)
                            
                        retry_count += 1
                        
                    if not transactions_to_process:
                        logger.info(f"Batch {fromBlock}-{toBlock} completed successfully")
                    else:
                        logger.error(f"Batch {fromBlock}-{toBlock} completed with {len(transactions_to_process)} permanently failed transactions")

        # Check if any transactions failed permanently and raise exception
        if all_failed_transactions:
            logger.error(f"Sync completed with {len(all_failed_transactions)} permanently failed transactions out of {total_transactions_attempted} attempted")
            raise TransactionSyncError(all_failed_transactions, total_transactions_attempted)
        
        logger.info(f"Sync completed successfully. All {total_transactions_attempted} transactions processed.")




