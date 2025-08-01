import logging
import json
from datetime import datetime
from ..database.utils import get_db_connection
from ..data_types import MetaDataStructure, BlockchainBlockHeightsStructure, VerticesAspectDataStructure

# Configure logging
logger = logging.getLogger(__name__)



class RawDataSelector:
    """
    Class for fetching raw data from the database.

    This class provides methods to retrieve various types of data from the database,
    such as the first blocks of each month or node capacities and channel counts at specific block heights.
    """


    def get_first_blocks_of_days_by_date_mask(self, dateMask=None, startSince='2018-01-01', endUntil='2050-01-01'):
        """
        Retrieves the block heights of the first block for each first day of the month.
        For example:
            - If the date mask is '20XX-03-01', the function will retrieve 2018-03-01, 2019-03-01, 2020-03-01, etc.
            - If the date mask is '20XX-XX-01', the function will retrieve 2018-01-01, 2018-02-01, 2018-03-01, etc.

        :param dateMask: str - The date mask to retrieve data from (format: 'XX-MM-DD').
        :param startSince: str - The start date to retrieve data from (format: 'YYYY-MM-DD').
        :param endUntil: str - The end date to retrieve data from (format: 'YYYY-MM-DD').
        :return: BlockchainBlockHeights - Data structure containing metadata and block heights.
        """

        # Adjust the dateMask for SQL LIKE clause
        sql_date_mask = dateMask.replace('X', '_')

        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                # Retrieve all dates that match the given date mask
                db_cursor.execute('''
                    SELECT 
                        BlockHeight, 
                        Date,
                        Timestamp
                    FROM 
                        Blockchain_Blocks
                    WHERE 
                        (Date, BlockHeight) IN (
                            SELECT 
                                Date, 
                                MIN(BlockHeight) AS BlockHeight
                            FROM 
                                Blockchain_Blocks
                            WHERE 
                                Date >= %s
                                AND Date <= %s
                                AND Date LIKE %s
                            GROUP BY Date
                        )
                    ORDER BY Date;
                ''', [startSince, endUntil, sql_date_mask])
                rows = db_cursor.fetchall()
                
                data = {
                    str(row['BlockHeight']): BlockchainBlockHeightsStructure.BlockData(
                        date=str(row['Date']),
                        timestamp=str(row['Timestamp'])
                    ) for row in rows
                }
                
                meta = MetaDataStructure(
                    type="BlockchainBlockHeights",
                    description=f"First blockchain block heights which have been mined at every date matching {dateMask}",
                    updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    xAxis="Date",
                    yAxis="BlockHeight",
                    yAxisSupplyChain=[]
                )
                
                return BlockchainBlockHeightsStructure(meta=meta, data=data)



    def get_first_blocks_of_months(self, withMeta=False, startSince='2018-01-01', endUntil='9999-12-31'):
        """
        Retrieves the block heights of the first block for each first day of the month.

        :param withMeta: bool - Whether to return metadata (True) or just the block heights (False).
        :param startSince: str - The start date to retrieve data from (format: 'YYYY-MM-DD').
        :param endUntil: str - The end date to retrieve data from (format: 'YYYY-MM-DD').
        :return: BlockchainBlockHeights - Data structure containing metadata and block heights.
        """
        
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                db_cursor.execute('''
                    SELECT 
                        BlockHeight, 
                        Date,
                        Timestamp
                    FROM 
                        Blockchain_Blocks
                    WHERE 
                        (Date, BlockHeight) IN (
                            SELECT 
                                Date, 
                                MIN(BlockHeight) AS BlockHeight
                            FROM 
                                Blockchain_Blocks
                            WHERE 
                                DAY(Date) = 1
                                AND Date >= %s
                                AND Date <= %s
                            GROUP BY Date
                        )
                    ORDER BY Date;
                ''', [startSince, endUntil])
                rows = db_cursor.fetchall()
                
                data = {
                    str(row['BlockHeight']): BlockchainBlockHeightsStructure.BlockData(
                        date=str(row['Date']),
                        timestamp=str(row['Timestamp'])
                    ) for row in rows
                }
                
                if withMeta:
                    meta = MetaDataStructure(
                        type="BlockchainBlockHeights",
                        description="First blockchain block heights which have been mined at every month of BLN lifetime",
                        xAxis="Date",
                        yAxis="BlockHeight",
                        yAxisSupplyChain=[]
                    )
                    return BlockchainBlockHeightsStructure(meta=meta, data=data)
                else:
                    return data
        


    def get_ln_nodes_capacities(self, blockHeight):
        """
        Fetches the capacities of LN nodes at a specific block height.
        
        A channel is considered active at a given block height if:
        - It was opened (funded) on or before the block (FundingBlockIndex <= blockHeight),
        - It closes (is spent) after the block (SpendingBlockIndex > blockHeight).
        
        This method sums up the capacity (transaction value) for both positions (NodeID1 and NodeID2)
        across all active channels at the given block height.
        
        :param blockHeight: int - The block height at which channels are active.
        :return: list of dicts - Each dict contains 'NodeID' and 'NodeValue', representing the total 
                                 capacity attributed to that node.
        """
        with get_db_connection() as db_conn:
            # Using a dictionary-based cursor for clearer column references
            with db_conn.cursor(dictionary=True) as db_cursor:
                query = '''
                    SELECT NodeID, SUM(Value) AS NodeValue FROM (
                        SELECT LC.NodeID1 AS NodeID, BT.Value AS Value
                        FROM Lightning_Channels LC
                        JOIN Blockchain_Transactions BT 
                          ON LC.ShortChannelID = BT.ShortChannelID
                        WHERE BT.FundingBlockIndex <= %s
                          AND BT.SpendingBlockIndex > %s
                        
                        UNION ALL
                        
                        SELECT LC.NodeID2 AS NodeID, BT.Value AS Value
                        FROM Lightning_Channels LC
                        JOIN Blockchain_Transactions BT 
                          ON LC.ShortChannelID = BT.ShortChannelID
                        WHERE BT.FundingBlockIndex <= %s
                          AND BT.SpendingBlockIndex > %s
                    ) AS combined
                    GROUP BY NodeID;
                '''
                logger.debug("Executing LN nodes capacities query for blockHeight: %s", blockHeight)
                # We pass the blockHeight twice for each subquery's condition (total four parameters)
                db_cursor.execute(query, (blockHeight, blockHeight, blockHeight, blockHeight))
                result = db_cursor.fetchall()
                logger.debug("LN nodes capacities result: %s", result)
                return [{'NodeID': row['NodeID'], 'NodeValue': row['NodeValue']} for row in result]



    def get_ln_nodes_channel_counts(self, blockHeight):
        """
        Fetches the channel counts of LN nodes at a specific block height.
        
        A channel is considered active at a given block height if:
        - It was opened (funded) on or before the block (FundingBlockIndex <= blockHeight),
        - It closes (is spent) after the block (SpendingBlockIndex > blockHeight).
        
        This method counts the number of active channels that each node participates in, 
        taking into account that a node might appear as either NodeID1 or NodeID2.
        
        :param blockHeight: int - The block height at which channels are active.
        :return: list of dicts - Each dict contains 'NodeID' and 'ChannelCount'.
        """
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                query = '''
                    SELECT NodeID, COUNT(*) AS ChannelCount FROM (
                        SELECT LC.NodeID1 AS NodeID
                        FROM Lightning_Channels LC
                        JOIN Blockchain_Transactions BT 
                          ON LC.ShortChannelID = BT.ShortChannelID
                        WHERE BT.FundingBlockIndex <= %s
                          AND BT.SpendingBlockIndex > %s
                        
                        UNION ALL
                        
                        SELECT LC.NodeID2 AS NodeID
                        FROM Lightning_Channels LC
                        JOIN Blockchain_Transactions BT 
                          ON LC.ShortChannelID = BT.ShortChannelID
                        WHERE BT.FundingBlockIndex <= %s
                          AND BT.SpendingBlockIndex > %s
                    ) AS combined
                    GROUP BY NodeID;
                '''
                logger.debug("Executing LN nodes channel counts query for blockHeight: %s", blockHeight)
                db_cursor.execute(query, (blockHeight, blockHeight, blockHeight, blockHeight))
                result = db_cursor.fetchall()
                logger.debug("LN nodes channel counts result: %s", result)
                return [{'NodeID': row['NodeID'], 'ChannelCount': row['ChannelCount']} for row in result]



