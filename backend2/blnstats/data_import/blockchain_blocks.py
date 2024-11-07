# data_import/blockchain_blocks.py

import logging
from multiprocessing import Pool
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from ..database.utils import get_db_connection
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def retrieve_and_write_blockchain_block(args):
    """
    Retrieves block data from the Bitcoin node and writes it to the database.

    :param args: Tuple containing (height, rpc_credentials)
    """
    height, rpc_credentials = args
    btc_rpc_user = rpc_credentials['user']
    btc_rpc_password = rpc_credentials['password']
    btc_rpc_ip = rpc_credentials['ip']
    btc_rpc_port = rpc_credentials['port']

    try:
        rpc_connection = AuthServiceProxy(f"http://{btc_rpc_user}:{btc_rpc_password}@{btc_rpc_ip}:{btc_rpc_port}")
        block_hash = rpc_connection.getblockhash(height)
        block = rpc_connection.getblock(block_hash)
        timestamp = block['time']
        dt_object = datetime.fromtimestamp(timestamp)
        human_readable_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        human_readable_date = human_readable_time.split()[0]

        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                db_cursor.execute('''
                    INSERT INTO `Blockchain_Blocks` (
                        `BlockHeight`, `BlockHash`, `Timestamp`, `Time`, `Date`
                    ) VALUES (%s, %s, %s, %s, %s)
                ''', (
                    height,
                    block_hash,
                    timestamp,
                    human_readable_time,
                    human_readable_date
                ))
                db_conn.commit()
        logger.info(f"Block {height} inserted into database.")
    except JSONRPCException as e:
        logger.error(f"JSONRPCException retrieving block at height {height}: {e}")
    except Exception as e:
        logger.error(f"Error retrieving block at height {height}: {e}")




class BlockchainBlocks:
    """
    Class to handle importing blockchain block data into the database.
    """

    def __init__(self, btc_rpc_user: str, btc_rpc_password: str, btc_rpc_ip: str, btc_rpc_port: int):
        """
        Initializes the BlockchainBlocks class with Bitcoin RPC credentials.

        :param btc_rpc_user: Bitcoin RPC username.
        :param btc_rpc_password: Bitcoin RPC password.
        :param btc_rpc_ip: Bitcoin RPC IP address.
        :param btc_rpc_port: Bitcoin RPC port.
        """
        self.btc_rpc_user = btc_rpc_user
        self.btc_rpc_password = btc_rpc_password
        self.btc_rpc_ip = btc_rpc_ip
        self.btc_rpc_port = btc_rpc_port

        # Initialize RPC connection
        self.rpc_connection = AuthServiceProxy(f"http://{btc_rpc_user}:{btc_rpc_password}@{btc_rpc_ip}:{btc_rpc_port}")

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
        Syncs missing blocks from the Bitcoin node into the database.
        """
        try:
            # Get the latest block height from the Bitcoin node
            latest_blockchain_height = self.rpc_connection.getblockcount()

            rpc_credentials = {
                'user': self.btc_rpc_user,
                'password': self.btc_rpc_password,
                'ip': self.btc_rpc_ip,
                'port': self.btc_rpc_port
            }

            processes = 4  # Number of worker processes
            batch_size = 10000  # Number of blocks to process in each batch

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

                tasks = [(height, rpc_credentials) for height in missing_heights]

                while True:
                    try:
                        with Pool(processes=processes) as pool:
                            pool.map(retrieve_and_write_blockchain_block, tasks)
                        break  # Break the while loop if successful
                    except Exception as e:
                        logger.error(f"Error syncing blocks {batch_start} to {batch_end}: {e}")
                        continue

        except JSONRPCException as e:
            logger.error(f"JSONRPCException: {e}")
        except Exception as e:
            logger.error(f"Error initializing sync: {e}")
