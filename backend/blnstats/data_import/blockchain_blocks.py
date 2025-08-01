import logging
import socket
import json
import hashlib
import time
from multiprocessing import Pool
from ..database.utils import get_db_connection
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlockSyncError(Exception):
    """Exception raised when blocks fail to sync after all retry attempts."""
    
    def __init__(self, failed_blocks: Dict[int, str], total_blocks_attempted: int):
        self.failed_blocks = failed_blocks
        self.total_blocks_attempted = total_blocks_attempted
        self.failed_count = len(failed_blocks)
        
        message = (f"Failed to sync {self.failed_count} out of {total_blocks_attempted} blocks. "
                  f"Failed block heights: {list(failed_blocks.keys())}")
        super().__init__(message)


def send_electrum_request(server_ip: str, server_port: int, method: str, params: list):
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
        logger.error(f"Error from Electrum server: {response_json['error']['message']}")
        return None

    return response_json.get('result')


def get_block_hash_from_header(header_hex: str) -> str:
    header_bytes = bytes.fromhex(header_hex)
    hash1 = hashlib.sha256(header_bytes).digest()
    hash2 = hashlib.sha256(hash1).digest()
    return hash2[::-1].hex()


def retrieve_and_write_blockchain_block(args):
    """
    Retrieves block data from the Electrum server and writes it to the database.

    :param args: Tuple containing (height, electrum_credentials)
    :return: Tuple of (height, success_status, error_message)
    """
    height, electrum_credentials = args
    electrum_host = electrum_credentials['host']
    electrum_port = electrum_credentials['port']

    try:
        raw_header = send_electrum_request(electrum_host, electrum_port, 'blockchain.block.header', [height])
        if not raw_header:
            logger.error(f"Could not retrieve header for block {height}")
            return (height, False, "Could not retrieve header")

        block_hash = get_block_hash_from_header(raw_header)

        # The block header is an 80-byte structure.
        # The timestamp is a 4-byte little-endian integer located at bytes 68-71.
        header_bytes = bytes.fromhex(raw_header)
        timestamp = int.from_bytes(header_bytes[68:72], 'little')

        dt_object = datetime.fromtimestamp(timestamp)
        human_readable_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        human_readable_date = human_readable_time.split()[0]

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                db_cursor.execute('''
                    INSERT INTO `Blockchain_Blocks` 
                        (`BlockHeight`, `BlockHash`, `Timestamp`, `Time`, `Date`) VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        BlockHash = VALUES(BlockHash),
                        Timestamp = VALUES(Timestamp),
                        Time = VALUES(Time),
                        Date = VALUES(Date)
                ''', (
                    height,
                    block_hash,
                    timestamp,
                    human_readable_time,
                    human_readable_date
                ))
                db_conn.commit()
        
        logger.info(f"Block {height} inserted into database.")
        return (height, True, None)
        
    except Exception as e:
        error_msg = f"Error processing block {height}: {str(e)}"
        logger.error(error_msg)
        return (height, False, error_msg)



class BlockchainBlocks:
    """
    Class to handle importing blockchain block data into the database.
    """


    def __init__(self, electrum_host: str, electrum_port: int):
        """
        Initializes the BlockchainBlocks class with Electrum server credentials.

        :param electrum_host: Electrum server IP address.
        :param electrum_port: Electrum server port.
        """
        self.electrum_host = electrum_host
        self.electrum_port = electrum_port

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                self.__create_tables_if_not_exist(db_cursor)



    def __create_tables_if_not_exist(self, db_cursor):
        """
        Creates the Blockchain_Blocks table if it does not exist.
        """
        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS `Blockchain_Blocks` (
                `BlockHeight` INT UNSIGNED NOT NULL UNIQUE,
                `BlockHash` CHAR(64) NOT NULL,
                `Timestamp` INT UNSIGNED NOT NULL,
                `Time` DATETIME NOT NULL,
                `Date` DATE NOT NULL,
                PRIMARY KEY (`BlockHeight`),
                INDEX `idx_BlockHash` (`BlockHash`),
                INDEX `idx_Timestamp` (`Timestamp`),
                INDEX `idx_Date` (`Date`)
            );
        ''')



    def sync_blocks(self):
        """
        Syncs missing blocks from the Electrum server into the database.
        
        :raises BlockSyncError: If any blocks fail to sync after all retry attempts
        """
        # Get the latest block height from the Electrum server
        latest_header = send_electrum_request(self.electrum_host, self.electrum_port, 'blockchain.headers.subscribe', [])
        if not latest_header:
            logger.error("Could not get latest block from Electrum server.")
            raise BlockSyncError({}, 0)
        latest_blockchain_height = latest_header['height']

        electrum_credentials = {
            'host': self.electrum_host,
            'port': self.electrum_port
        }

        processes = 4  # Number of worker processes
        batch_size = 10000  # Number of blocks to process in each batch
        max_retries = 10  # Maximum number of retries for failed blocks
        retry_delay = 15  # Delay in seconds before retrying failed blocks
        
        # Track overall sync results
        all_failed_blocks = {}  # height -> error_message
        total_blocks_attempted = 0

        # Iterate over the entire range of block heights in batches
        for batch_start in range(0, latest_blockchain_height + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, latest_blockchain_height)
            all_heights = list(range(batch_start, batch_end + 1))

            # Get existing BlockHeights in the batch from the database
            with get_db_connection() as db_conn:
                with db_conn.cursor() as db_cursor:
                    db_cursor.execute('''
                        SELECT `BlockHeight` FROM `Blockchain_Blocks`
                        WHERE `BlockHeight` BETWEEN %s AND %s
                    ''', (batch_start, batch_end))
                    existing_blocks = db_cursor.fetchall()
                    existing_heights = set(row[0] for row in existing_blocks)

            # Determine missing block heights in the batch
            missing_heights = [height for height in all_heights if height not in existing_heights]

            if not missing_heights:
                logger.info(f"All blocks from {batch_start} to {batch_end} already exist in the database. Skipping batch.")
                continue

            logger.info(f"Syncing missing blocks {missing_heights[0]} to {missing_heights[-1]} in batch {batch_start} to {batch_end}")
            total_blocks_attempted += len(missing_heights)

            # Track failed blocks for retry
            blocks_to_process = missing_heights
            retry_count = 0
            
            while blocks_to_process and retry_count < max_retries:
                tasks = [(height, electrum_credentials) for height in blocks_to_process]
                
                try:
                    with Pool(processes=processes) as pool:
                        results = pool.map(retrieve_and_write_blockchain_block, tasks)
                    
                    # Process results and identify failed blocks
                    successful_blocks = []
                    failed_blocks = []
                    
                    for height, success, error_msg in results:
                        if success:
                            successful_blocks.append(height)
                        else:
                            failed_blocks.append((height, error_msg))
                    
                    logger.info(f"Batch {batch_start}-{batch_end}: {len(successful_blocks)} successful, {len(failed_blocks)} failed")
                    
                    if failed_blocks:
                        logger.warning(f"Failed blocks in retry {retry_count + 1}: {[h for h, _ in failed_blocks]}")
                        if retry_count < max_retries - 1:
                            blocks_to_process = [h for h, _ in failed_blocks]
                            logger.info(f"Waiting {retry_delay} seconds before retrying {len(blocks_to_process)} failed blocks...")
                            time.sleep(retry_delay)
                        else:
                            # Log permanently failed blocks and add to overall tracking
                            for height, error_msg in failed_blocks:
                                logger.error(f"Block {height} permanently failed after {max_retries} attempts: {error_msg}")
                                all_failed_blocks[height] = error_msg
                    else:
                        blocks_to_process = []  # All blocks successful
                        
                except Exception as e:
                    logger.error(f"Pool error syncing blocks {batch_start} to {batch_end} (attempt {retry_count + 1}): {e}")
                    if retry_count < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying due to pool error...")
                        time.sleep(retry_delay)
                    
                retry_count += 1
                
            if not blocks_to_process:
                logger.info(f"Batch {batch_start}-{batch_end} completed successfully")
            else:
                logger.error(f"Batch {batch_start}-{batch_end} completed with {len(blocks_to_process)} permanently failed blocks")

        # Check if any blocks failed permanently and raise exception
        if all_failed_blocks:
            logger.error(f"Sync completed with {len(all_failed_blocks)} permanently failed blocks out of {total_blocks_attempted} attempted")
            raise BlockSyncError(all_failed_blocks, total_blocks_attempted)
        
        logger.info(f"Sync completed successfully. All {total_blocks_attempted} blocks synced.")
