import logging
from datetime import datetime
from ..database.utils import get_db_connection
from ..data_types import VerticesAspectDataStructure, BlockchainBlockHeightsStructure



# Configure logging
logger = logging.getLogger(__name__)



class EntityMetricsSelector:
    '''
    Class for fetching preprocessed entity metrics from the database such as channel counts and capacities at specific block heights.
    '''


    def get_channel_count_metrics(self, blockHeightsStructure: BlockchainBlockHeightsStructure):
        """
        Retrieves the channel count metrics of Lightning Network entities at specific block heights.
        
        :param blockHeightsStructure: BlockchainBlockHeightsStructure - A data structure containing block heights.
        :return: VerticesAspectDataStructure - A data structure containing entity names and their channel counts.
        """

        # Extract block heights
        blockHeights = list(blockHeightsStructure.data.keys())

        # Initialize the VerticesAspectDataStructure with metadata
        results = VerticesAspectDataStructure(
            meta={
                "type": "VerticesAspectDataStructure",
                "description": "Entities channel counts on given block heights",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "xAxis": "BlockHeight",
                "yAxis": "List(EntityName,ChannelCount)",
                "yAxisSupplyChain": ["BlockHeight"]
            },
            data={}
        )

        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                for blockHeight in blockHeights:
                    
                    db_cursor.execute('''
                        SELECT 
                            Lightning_Entities.EntityName,
                            SUM(_CACHED1_NodeMetrics.ChannelCount) AS ChannelCount
                        FROM
                            _CACHED1_NodeMetrics
                        LEFT JOIN Lightning_Entities 
                            ON _CACHED1_NodeMetrics.NodeID = Lightning_Entities.NodeID
                        WHERE 
                            BlockHeight = %s
                        GROUP BY Lightning_Entities.EntityName
                    ''',
                        (blockHeight,)
                    )
                    
                    rows = db_cursor.fetchall()
                    vertices = []
                    for row in rows:
                        # Create VerticeData instances
                        vertex = VerticesAspectDataStructure.VerticeData(name=row['EntityName'], value=int(row['ChannelCount']))
                        vertices.append(vertex)
                    
                    # Add the vertices data to the results
                    results.data[str(blockHeight)] = VerticesAspectDataStructure.VerticeEntry(
                        date=blockHeightsStructure.data[blockHeight].date,
                        timestamp=blockHeightsStructure.data[blockHeight].timestamp,
                        vertices=vertices
                    )
        
        return results





    def get_capacity_metrics(self, blockHeightsStructure: BlockchainBlockHeightsStructure):
        """
        Retrieves the capacity metrics of Lightning Network entities at specific block heights.
        
        :param blockHeightsStructure: BlockchainBlockHeightsStructure - A data structure containing block heights.
        :return: VerticesAspectDataStructure - A data structure containing entity names and their capacities.
        """

        # Extract block heights
        blockHeights = list(blockHeightsStructure.data.keys())

        # Initialize the VerticesAspectDataStructure with metadata
        results = VerticesAspectDataStructure(
            meta={
                "type": "VerticesAspectDataStructure",
                "description": "Entities capacities on given block heights",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "xAxis": "BlockHeight",
                "yAxis": "List(EntityName,Capacity)",
                "yAxisSupplyChain": ["BlockHeight"]
            },
            data={}
        )
        
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                for blockHeight in blockHeights:
                    
                    db_cursor.execute('''
                        SELECT 
                            Lightning_Entities.EntityName,
                            SUM(_CACHED1_NodeMetrics.Capacity) AS Capacity
                        FROM
                            _CACHED1_NodeMetrics
                        LEFT JOIN Lightning_Entities 
                            ON _CACHED1_NodeMetrics.NodeID = Lightning_Entities.NodeID
                        WHERE 
                            BlockHeight = %s
                        GROUP BY Lightning_Entities.EntityName
                    ''',
                        (blockHeight,)
                    )
                    
                    rows = db_cursor.fetchall()
                    vertices = []
                    for row in rows:
                        # Create VerticeData instances
                        vertex = VerticesAspectDataStructure.VerticeData(name=row['EntityName'], value=int(row['Capacity']))
                        vertices.append(vertex)
                    
                    # Add the vertices data to the results
                    results.data[str(blockHeight)] = VerticesAspectDataStructure.VerticeEntry(
                        date=blockHeightsStructure.data[blockHeight].date,
                        timestamp=blockHeightsStructure.data[blockHeight].timestamp,
                        vertices=vertices
                    )
        
        return results