# data_transform/node_metrics.py

import logging
from ..database.utils import get_db_connection
from ..database.raw_data_selector import RawDataSelector

# Configure logging
logger = logging.getLogger(__name__)



class NodeMetrics:
    """
    Class to handle the transformation of node metrics.

    This class is responsible for processing and storing node metrics data, including
    capacities and channel counts, for specific block heights or the first blocks of each month.
    """


    def __init__(self):
        """
        Initializes the NodeMetrics class and creates the necessary table if it doesn't exist.
        """
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:
                db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS `_CACHED1_NodeMetrics` (
                        `BlockHeight` INTEGER NOT NULL,
                        `NodeID` VARCHAR(66) NOT NULL,
                        `ChannelCount` INTEGER NOT NULL,
                        `Capacity` BIGINT NOT NULL,
                        PRIMARY KEY (`BlockHeight`, `NodeID`),
                        INDEX idx_blockheight (`BlockHeight`),
                        INDEX idx_nodeid (`NodeID`)
                    );
                ''')
        self.raw_data_selector = RawDataSelector()
        logger.info("NodeMetrics table initialized.")




    def transformForBlockHeight(self, blockHeight):
        """
        Transforms and stores the node metrics for a specific block height.

        :param blockHeight: int - The block height to process.
        """
        blockHeight = int(blockHeight)
        logger.info(f"Processing BlockHeight: {blockHeight}")

        # Get capacities
        capacities = self.raw_data_selector.get_ln_nodes_capacities(blockHeight)

        # Get channel counts
        channel_counts = self.raw_data_selector.get_ln_nodes_channel_counts(blockHeight)

        # Merge data
        node_metrics = {}

        for cap in capacities:
            NodeID = cap['NodeID']
            NodeValue = int(cap['NodeValue'])
            node_metrics[NodeID] = {'Capacity': NodeValue}

        for cnt in channel_counts:
            NodeID = cnt['NodeID']
            ChannelCount = int(cnt['ChannelCount'])
            if NodeID in node_metrics:
                node_metrics[NodeID]['ChannelCount'] = ChannelCount
            else:
                node_metrics[NodeID] = {'ChannelCount': ChannelCount, 'Capacity': 0}

        # Ensure all nodes have both Capacity and ChannelCount
        for NodeID, metrics in node_metrics.items():
            metrics.setdefault('ChannelCount', 0)
            metrics.setdefault('Capacity', 0)

        # Insert data into `_CACHED1_NodeMetrics` table
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                # Delete data for this block height
                db_cursor.execute('''
                    DELETE FROM `_CACHED1_NodeMetrics` WHERE `BlockHeight` = %s
                ''', (blockHeight,))
                db_conn.commit()

                data_to_insert = []
                for NodeID, metrics in node_metrics.items():
                    ChannelCount = metrics['ChannelCount']
                    Capacity = metrics['Capacity']
                    data_to_insert.append((blockHeight, NodeID, ChannelCount, Capacity))

                # Insert data in batches if necessary
                batch_size = 10000
                for i in range(0, len(data_to_insert), batch_size):
                    batch = data_to_insert[i:i + batch_size]
                    db_cursor.executemany('''
                        INSERT INTO `_CACHED1_NodeMetrics` (`BlockHeight`, `NodeID`, `ChannelCount`, `Capacity`)
                        VALUES (%s, %s, %s, %s)
                    ''', batch)
                    db_conn.commit()

        logger.info(f"Successfully processed BlockHeight: {blockHeight}")




    def transformForFirstBlocksOfMonths(self):
        """
        Transforms and stores the node metrics for the first block of each month.
        """
        first_blocks = self.raw_data_selector.get_first_blocks_of_months(withMeta=False)
        if not first_blocks:
            logger.warning("No first blocks found. Ensure the Blockchain_Blocks table is populated.")
            return

        for blockHeight in first_blocks:
            self.transformForBlockHeight(blockHeight)


