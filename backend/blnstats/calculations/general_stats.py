from datetime import datetime
from ..data_types import VerticesAspectDataStructure, GeneralStatsDataStructure
from ..database.utils import get_db_connection
import json
import os


class GeneralStats:


    def calculate(self, vertices_capacity_data: VerticesAspectDataStructure, vertices_channel_count_data: VerticesAspectDataStructure):
        
        # Check incoming data for consistency
        if(vertices_capacity_data.meta.yAxis != "List(NodeID,Capacity)"):
            raise ValueError("VerticesCapacityDataStructure must have a yAxis of 'List(NodeID,Capacity)'")
        if(vertices_channel_count_data.meta.yAxis != "List(NodeID,ChannelCount)"):
            raise ValueError("VerticesChannelCountDataStructure must have a yAxis of 'List(NodeID,ChannelCount)'")
        if(len(vertices_capacity_data.data.values()) != len(vertices_channel_count_data.data.values())):
            raise ValueError("VerticesCapacityDataStructure and VerticesChannelCountDataStructure must have the same length")
        if(list(vertices_capacity_data.data.keys())[0] != list(vertices_channel_count_data.data.keys())[0]):
            raise ValueError("VerticesCapacityDataStructure and VerticesChannelCountDataStructure must start with the same block height")
        if(list(vertices_capacity_data.data.keys())[-1] != list(vertices_channel_count_data.data.keys())[-1]):
            raise ValueError("VerticesCapacityDataStructure and VerticesChannelCountDataStructure must end with the same block height")


        # Get block height data
        block_height_data = [block_height for block_height, vertices in vertices_capacity_data.data.items()]

        # Get date for each block height
        date_data = [item.date for item in vertices_capacity_data.data.values()]

        # Get timestamp for each block height
        timestamp_data = [item.timestamp for item in vertices_capacity_data.data.values()]

        # Get the node count for each block height
        node_count_data = [len(item.vertices) for item in vertices_capacity_data.data.values()]

        # Get the node capacity sum for each block height:
        #   - For a general sum of capacities we need to divide by 2 because each 
        #     channel is counted twice (one for each node)
        node_capacity_sum_data = [sum(vertice.value / (2 * 100000000) for vertice in vertices_entry.vertices)
                for vertices_entry in vertices_capacity_data.data.values()]

        # Get the channel count sum for each block height:
        #   - For a general count of channels we need to divide by 2 because 
        #     each channel is counted twice (one for each node)
        channel_count_sum_data = [sum(vertice.value / 2 for vertice in vertices_entry.vertices) 
                for vertices_entry in vertices_channel_count_data.data.values()]
        

        general_stats_data = GeneralStatsDataStructure(
            meta={
                "type": "GeneralStatsDataStructure",
                "description": "General stats for the BLN network",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "xAxis": "Date",
                "yAxis": "ChannelCount,NodeCount,NetworkCapacity",
                "yAxisSupplyChain": [
                    "BlockHeight",
                    "List(NodeID,Capacity),List(NodeID,ChannelCount)"
                ]
            },
            data={
                block_height_data[i]: GeneralStatsDataStructure.GeneralStatsData(
                    date=date_data[i],
                    timestamp=timestamp_data[i],
                    node_count=node_count_data[i],
                    network_capacity=node_capacity_sum_data[i],
                    channel_count=channel_count_sum_data[i]
                ) for i in range(len(block_height_data))
            }
        )

        return general_stats_data






    def calculate_channel_lifetime_plot(self):
        '''
        This method calculates distribution of channel lifetimes.
        X axis: Channel lifetime in days
        Y axis: Number of channels
        '''
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                query = '''
                    SELECT 
                        CASE 
                            WHEN BT.SpendingBlockIndex = 999999999 THEN 
                                (SELECT MAX(BlockHeight) FROM Blockchain_Blocks) - BT.FundingBlockIndex
                            ELSE 
                                BT.SpendingBlockIndex - BT.FundingBlockIndex
                        END AS ChannelLifetime
                    FROM 
                        Lightning_Channels LC
                    LEFT JOIN Blockchain_Transactions BT
                        ON LC.ShortChannelID = BT.ShortChannelID
                    WHERE
                        BT.FundingBlockIndex IS NOT NULL AND 
                        BT.SpendingBlockIndex IS NOT NULL AND
                        (BT.SpendingBlockIndex > BT.FundingBlockIndex OR BT.SpendingBlockIndex = 999999999)
                '''
                db_cursor.execute(query)
                results = db_cursor.fetchall()
                
                # Extract channel lifetimes and convert to days (assuming blocks per day conversion)
                # Note: You may need to adjust the blocks_per_day conversion based on your blockchain
                blocks_per_day = 144  # Typical for Bitcoin, adjust as needed
                lifetimes_days = [row['ChannelLifetime'] / blocks_per_day for row in results if row['ChannelLifetime'] is not None]
                
                # Create histogram bins - group by day ranges
                from collections import Counter
                import math
                
                # Round to nearest day and count occurrences
                lifetime_counts = Counter(math.floor(lifetime) for lifetime in lifetimes_days if lifetime >= 0)
                
                # Create sorted list of (lifetime_days, count) pairs
                total_channel_count = 0
                plot_data = {}
                if lifetime_counts:
                    max_lifetime = max(lifetime_counts.keys())
                    for day in range(0, max_lifetime + 1):
                        count = lifetime_counts.get(day, 0)
                        if count > 0:  # Only include days that have channels
                            plot_data[day] = {
                                'lifetime_days': day,
                                'channel_count': count
                            }
                            total_channel_count += count
                
                print(total_channel_count)

                data = {
                    'meta': {
                        'type': 'ChannelLifetimePlot',
                        'description': 'Distribution of Lightning channel lifetimes',
                        'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'xAxis': 'Channel lifetime (days)',
                        'yAxis': 'Number of channels',
                        'total_channels': len(lifetimes_days)
                    },
                    'data': plot_data
                }
                
                os.makedirs('/DATA/GENERATED/General_Stats/Channel_Lifetime', exist_ok=True)
                with open('/DATA/GENERATED/General_Stats/Channel_Lifetime/channel_lifetime_plot.json', 'w') as f:
                    json.dump(data, f, indent=4)




    def calculate_channel_lifetime_average(self):
        with get_db_connection() as db_conn:
            with db_conn.cursor(dictionary=True) as db_cursor:
                query = '''
                    SELECT 
                        AVG(
                            CASE 
                                WHEN BT.SpendingBlockIndex = 999999999 THEN 
                                    (SELECT MAX(BlockHeight) FROM Blockchain_Blocks) - BT.FundingBlockIndex
                                ELSE 
                                    BT.SpendingBlockIndex - BT.FundingBlockIndex
                            END
                        ) AS AverageChannelLifetime
                    FROM 
                        Lightning_Channels LC
                    LEFT JOIN Blockchain_Transactions BT
                        ON LC.ShortChannelID = BT.ShortChannelID
                    WHERE
                        BT.FundingBlockIndex IS NOT NULL AND 
                        BT.SpendingBlockIndex IS NOT NULL
                '''
                db_cursor.execute(query)
                result = db_cursor.fetchone()
                print(result['AverageChannelLifetime'])

                # Convert Decimal to float for JSON serialization
                avg_lifetime = float(result['AverageChannelLifetime']) if result['AverageChannelLifetime'] is not None else 0

                data = {
                    'meta': {
                        'type': 'ChannelLifetimeAverage',
                        'description': 'Average channel lifetime',
                        'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'average_channel_lifetime': avg_lifetime
                    },
                    'data': {
                        'average_channel_lifetime_blocks': avg_lifetime,
                        'average_channel_lifetime_days': avg_lifetime / 144
                    }
                }

                os.makedirs('/DATA/GENERATED/General_Stats/Channel_Lifetime', exist_ok=True)
                with open('/DATA/GENERATED/General_Stats/Channel_Lifetime/channel_lifetime_average.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return result['AverageChannelLifetime']
