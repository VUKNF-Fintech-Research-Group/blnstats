from datetime import datetime
from ..data_types import VerticesAspectDataStructure, GeneralStatsDataStructure



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










