from typing import Dict, List
from pydantic import BaseModel
import os
import json
import logging
import csv

# Configure logging
logger = logging.getLogger(__name__)



class MetaDataStructure(BaseModel):
    type: str
    description: str
    updated: str
    xAxis: str
    yAxis: str
    yAxisSupplyChain: List[str]




class BaseBLNDataStructure(BaseModel):
    '''
    Base class for all BLN data structures.

    Example:
    {
        "meta": {
            "type": "BlockchainBlockHeights",
            "description": "First blockchain block heights which have been mined at every month of BLN lifetime",
            "xAxis": "Date",
            "yAxis": "BlockHeight",
            "yAxisSupplyChain": []
        },
        ...
    }
    '''
    meta: MetaDataStructure


    def save_to_file(self, filePath: str):
        os.makedirs(os.path.dirname(filePath), exist_ok=True)
        with open(filePath, 'w') as file:
            json.dump(json.loads(self.json()), file, indent=4)


    def to_json_obj(self):
        """
        Returns structure as JSON object.
        """
        return json.loads(self.json())

    def to_json_str(self):
        """
        Returns structure as JSON string.
        """
        return self.json()







# Data structure for BlockchainBlockHeights
class BlockchainBlockHeightsStructure(BaseBLNDataStructure):
    '''
    Example:
    {
        "meta": {
            "type": "BlockchainBlockHeights",
            "description": "First blockchain block heights which have been mined at every month of BLN lifetime",
            "xAxis": "Date",
            "yAxis": "BlockHeight",
            "yAxisSupplyChain": []
        },
        "data": {
            "510123": {
                "date": "2018-01-01",
                "timestamp": "65465465465"
            },
            "520456": {
                "date": "2018-02-01",
                "timestamp": "65465465465"
            },
            "530789": {
                "date": "2018-03-01",
                "timestamp": "65465465465"
            }
        }
    }
    '''
    class BlockData(BaseModel):
        date: str
        timestamp: int

    data: Dict[str, BlockData]






# Data structure for:
#   - NodesCapacities
#   - NodesChannelCounts
#   - EntitiesCapacities
#   - EntitiesChannelCounts
# for a given block height or block heights
class VerticesAspectDataStructure(BaseBLNDataStructure):
    '''
    Example for NodesCapacities:
    {
        "meta": {
            "type": "VerticesAspectDataStructure",
            "description": "Nodes capacities on a given block heights",
            "xAxis": "BlockHeight",
            "yAxis": "List(NodeID,Capacity)",
            "yAxisSupplyChain": [
                "BlockHeight"
            ]
        },
        "data": {
            "505000": {
                "date": "2018-01-01",
                "timestamp": 1234567890,
                "vertices": [
                    {
                        "name": "0123456abcdef...0123456abcdef",
                        "value": 123456789
                    },
                    {
                        "name": "abcdefabcdef...abcdefabcdef",
                        "value": 987654321
                    }
                ]
            }
        }
    }
    '''
    class VerticeData(BaseModel):
        name: str
        value: int

    class VerticeEntry(BaseModel):
        date: str
        timestamp: int
        vertices: List['VerticesAspectDataStructure.VerticeData']

    data: Dict[str, VerticeEntry]



    def save_to_csv(self, filePath: str, divideValueBy: float = 1.0):
        """
        Saves the data to a CSV file.
        
        Example:
        name,value,date
        0123456abcdef...0123456abcdef,123456789,2018-01-01
        abcdefabcdef...abcdefabcdef,987654321,2018-01-01
        """

        jsonObject = self.to_json_obj()

        # Define the CSV file headers
        headers = ['name', 'value', 'date']

        # Open the file in write mode
        os.makedirs(os.path.dirname(filePath), exist_ok=True)
        with open(filePath, mode='w', newline='', encoding='utf-8') as file:

            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()

            # Iterate through all block heights
            for blockHeight in list(jsonObject['data'].keys()):
    
                singlePointVerticesObject = jsonObject['data'][blockHeight]

                date = singlePointVerticesObject['date']
                verticesData = singlePointVerticesObject['vertices']

                for vertex in verticesData:
                    if(divideValueBy != 1.0):
                        vertex['value'] = f"{vertex['value'] / divideValueBy:.8f}"
                    else:
                        vertex['value'] = vertex['value']

                    writer.writerow(
                        {
                            'name': vertex['name'],
                            'value': vertex['value'],
                            'date': date
                        }
                    )




# Data structure for CoefficientsAcrossTheTime
class CoefficientsDataStructure(BaseBLNDataStructure):
    '''
    Example:
    {
        "meta": {
            "type": "CoefficientsAcrossTheTime(Gini)",
            "description": "Gini Coefficients for nodes capacities at given block heights",
            "xAxis": "BlockHeight",
            "yAxis": "Gini",
            "yAxisSupplyChain": [
                "BlockHeight",
                "List(NodeID,Capacity)"
            ]
        },
        "data": {
            "505000": {
                "value": 0.123456,
                "date": "2018-02-01",
                "timestamp": 1234567890,
                "input_array_length": 10,
                "input_array_sum": 1234567890
            },
            "505001": {
                "value": 0.456789,
                "date": "2018-02-02",
                "timestamp": 1234567890,
                "input_array_length": 10,
                "input_array_sum": 1234567890
            },
            "505002": {
                "value": 0.789123,
                "date": "2018-02-03",
                "timestamp": 1234567890,
                "input_array_length": 10,
                "input_array_sum": 1234567890
            }
        }
    }
    '''
    class CoefficientData(BaseModel):
        date: str
        timestamp: int
        value: float
        input_array_length: int
        input_array_sum: int

    data: Dict[str, CoefficientData]





class GeneralStatsDataStructure(BaseBLNDataStructure):
    '''
    Example:
    {
        "meta": {
            "type": "GeneralStatsDataStructure",
            "description": "General stats for the BLN network",
            "xAxis": "Date",
            "yAxis": "List(NodeID,Capacity)",
            "yAxisSupplyChain": [
                "BlockHeight"
            ]
        },
        "data": {
            "505000": {
                "date": "2018-01-01",
                "timestamp": 1234567890,
                "node_count": 100,
                "network_capacity": 12.3456789,
                "channel_count": 200
            },
            "510000": {
                "date": "2018-02-01",
                "timestamp": 1234567890,
                "node_count": 150,
                "network_capacity": 21.3456789,
                "channel_count": 300
            }
        }
    }
    '''
    class GeneralStatsData(BaseModel):
        date: str
        timestamp: int
        node_count: int
        network_capacity: float
        channel_count: int

    data: Dict[str, GeneralStatsData]

