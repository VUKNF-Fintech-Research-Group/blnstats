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



    def get_first_blocks_of_months(self, withMeta=False, startSince='2018-01-01', endUntil='9999-99-99'):
        """
        Retrieves the block heights of the first block for each first day of the month.

        :param withMeta: bool - Whether to return metadata (True) or just the block heights (False).
        :param startSince: str - The start date to retrieve data from (format: 'YYYY-MM-DD').
        :return: BlockchainBlockHeights - Data structure containing metadata and block heights.
        """
        
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                # Retrieve all dates that are the first day of the month
                db_cursor.execute('''
                    SELECT 
                        MIN(BlockHeight) AS BlockHeight, 
                        Date,
                        Timestamp
                    FROM 
                        Blockchain_Blocks
                    WHERE 
                        DAY(Date) = 1
                        AND Date >= %s
                        AND Date <= %s
                    GROUP BY Date
                    ORDER BY Date;
                ''', [startSince, endUntil])
                rows = db_cursor.fetchall()
                
                data = {str(row['Date']): BlockchainBlockHeightsStructure.BlockData(value=row['BlockHeight']) for row in rows}
                
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
        


