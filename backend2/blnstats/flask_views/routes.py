from flask import request, jsonify, make_response, Response, redirect, send_file
from flask_restful import Resource, Api
from flask_cors import CORS
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json
import time
import numpy as np
from datetime import datetime, date, timedelta

from . import app
from ..database.db_utils import get_db_connection
from ..data_processing.blockchain_tx import BlockchainTx






@app.route('/api/update/chart/<string:dataset>', methods=['GET'])
def updateCharts_HTTPGET(dataset, backtrack=0, orgRoomID=-1):
    timeblocksize = '2500'

    with get_db_connection() as conn:
        chartTimeDelta = None

        if(timeblocksize.isnumeric()):
            timeblocksize = int(timeblocksize)
            chartTimeDelta = timedelta(days=timeblocksize)
            timeFrom = (datetime.now() - chartTimeDelta*(backtrack+1)).strftime("%Y-%m-%d %H:%M:%S")
            
        elif(timeblocksize.endswith('h')):
            timeblocksizehours = timeblocksize.replace("h", '')
            timeblocksize = 0
            if(timeblocksizehours.isnumeric()):
                timeblocksizehours = int(timeblocksizehours)
                chartTimeDelta = timedelta(hours=timeblocksizehours)
                timeFrom = (datetime.now() - chartTimeDelta*(backtrack+1)).strftime("%Y-%m-%d %H:%M:%S")

        timeUntil = (datetime.now() - chartTimeDelta*backtrack).strftime("%Y-%m-%d %H:%M:%S")
        print("[*] timeUntil: " + timeUntil)
        print("[*] timeFrom: " + timeFrom)

        SQL_datetimeIntervalList = f''' 
            DateList AS
            (
                WITH cte AS (
                    SELECT 0 AS d 
                    
                    UNION ALL
                    
                    SELECT d + 1 
                    FROM cte 
                    WHERE d <= ?
                )
                SELECT DATE('now', '+' || 1 || ' days') AS date
                
                UNION ALL
                
                SELECT DATE('now', '-' || d || ' days') AS date
                FROM cte
                ORDER BY date ASC
            ),
            datetimeList AS
            (
                SELECT date AS DT
                FROM DateList
            ),
            datetimeIntervalList AS
            (
                SELECT
                    LAG ( dt, 1, 0 ) OVER ( 
                    ORDER BY DT 
                    ) StartDate,
                    DT as EndDate
                FROM 
                    datetimeList
                WHERE
                    EndDate > ? AND
                    EndDate <= ? AND
                    EndDate >= '2018-01-01'
            ),
        '''

        if(dataset == 'channelcount'):
            dateNow = datetime.now().strftime("%Y-%m-%d")
            query = f'''
                WITH {SQL_datetimeIntervalList}
                CroppedChannelSessions AS
                (
                    SELECT
                        FundingBlock.Date       AS StartDate,
                        SpendingBlock.Date      AS EndDate,
                        short_channel_id
                    FROM
                        LNResearch_20230924_ChannelAnnouncement
                    LEFT JOIN Blockchain_Transactions
                        ON LNResearch_20230924_ChannelAnnouncement.short_channel_id = Blockchain_Transactions.ShortChannelID
                    LEFT JOIN Blockchain_Blocks AS FundingBlock
                        ON Blockchain_Transactions.FundingBlockIndex = FundingBlock.BlockIndex
                    LEFT JOIN Blockchain_Blocks AS SpendingBlock
                        ON Blockchain_Transactions.SpendingBlockIndex = SpendingBlock.BlockIndex
                    WHERE
                        EndDate > ?
                ),
                ChannelsChartData AS
                (
                    SELECT
                        datetimeIntervalList.StartDate                              AS Date,
                        COUNT(DISTINCT CroppedChannelSessions.short_channel_id)     AS Channels
                    FROM
                        datetimeIntervalList
                    LEFT JOIN CroppedChannelSessions
                        ON datetimeIntervalList.StartDate <= CroppedChannelSessions.EndDate AND CroppedChannelSessions.StartDate <= datetimeIntervalList.EndDate
                    
                    WHERE
                        datetimeIntervalList.StartDate <> 0 AND 
                        CroppedChannelSessions.short_channel_id IS NOT NULL
                    GROUP BY datetimeIntervalList.StartDate
                )
                
                INSERT OR REPLACE INTO _CACHED_Chart_ChannelCount
                SELECT ChannelsChartData.Date, ChannelsChartData.Channels FROM ChannelsChartData
            '''
            print(query)
            conn.execute(query, [(timeblocksize+1)*(backtrack+1), '2018-01-01', '2023-12-31', '2018-01-01' ])
            return  Response('Done', mimetype='application/json')




        elif(dataset == 'nodecount'):
            dateNow = datetime.now().strftime("%Y-%m-%d")
            query = f'''
                WITH {SQL_datetimeIntervalList}
                CroppedNodeSessions AS
                (
                    SELECT 
                        ChannelTable.NodeID AS NodeID,
                        FundingBlock.Date AS StartDate,
                        SpendingBlock.Date AS EndDate
                    FROM
                        (SELECT 
                            node_id_1 AS NodeID,
                            short_channel_id AS ShortChannelID
                        FROM
                            LNResearch_20230924_ChannelAnnouncement
                        GROUP BY NodeID

                        UNION ALL

                        SELECT 
                            node_id_2 AS NodeID,
                            short_channel_id AS ShortChannelID
                        FROM
                            LNResearch_20230924_ChannelAnnouncement
                        GROUP BY NodeID
                        ) AS ChannelTable
                    LEFT JOIN Blockchain_Transactions
                        ON Blockchain_Transactions.ShortChannelID = ChannelTable.ShortChannelID
                    LEFT JOIN Blockchain_Blocks AS FundingBlock
                        ON FundingBlock.BlockIndex = Blockchain_Transactions.FundingBlockIndex
                    LEFT JOIN Blockchain_Blocks AS SpendingBlock
                        ON SpendingBlock.BlockIndex = Blockchain_Transactions.SpendingBlockIndex
                ),
                NodesChartData AS
                (
                    SELECT
                        datetimeIntervalList.StartDate                  AS Date,
                        COUNT(DISTINCT CroppedNodeSessions.NodeID)      AS Nodes
                    FROM
                        datetimeIntervalList
                    LEFT JOIN CroppedNodeSessions
                        ON datetimeIntervalList.StartDate <= CroppedNodeSessions.EndDate AND CroppedNodeSessions.StartDate <= datetimeIntervalList.EndDate
                    
                    WHERE
                        datetimeIntervalList.StartDate <> 0 AND 
                        CroppedNodeSessions.NodeID IS NOT NULL
                    GROUP BY datetimeIntervalList.StartDate
                )
                
                INSERT OR REPLACE INTO _CACHED_Chart_NodeCount
                SELECT NodesChartData.Date, NodesChartData.Nodes FROM NodesChartData
            '''
            print(query)
            conn.execute(query, [(timeblocksize+1)*(backtrack+1), '2018-01-01', '2023-12-31' ])
            return  Response('Done', mimetype='application/json')





        elif(dataset == 'totalliquidity'):
            dateNow = datetime.now().strftime("%Y-%m-%d")
            query = f'''
                WITH {SQL_datetimeIntervalList}
                AllChannelSessions AS
                (
                    SELECT
                        FundingBlock.Date       AS StartDate,
                        SpendingBlock.Date      AS EndDate,
                        short_channel_id,
                        Blockchain_Transactions.Value AS Value
                    FROM
                        LNResearch_20230924_ChannelAnnouncement
                    LEFT JOIN Blockchain_Transactions
                        ON LNResearch_20230924_ChannelAnnouncement.short_channel_id = Blockchain_Transactions.ShortChannelID
                    LEFT JOIN Blockchain_Blocks AS FundingBlock
                        ON Blockchain_Transactions.FundingBlockIndex = FundingBlock.BlockIndex
                    LEFT JOIN Blockchain_Blocks AS SpendingBlock
                        ON Blockchain_Transactions.SpendingBlockIndex = SpendingBlock.BlockIndex
                    WHERE
                        EndDate > ?
                ),
                TotalLiquidityChartData AS
                (
                    SELECT
                        datetimeIntervalList.StartDate      AS Date,
                        CAST(SUM(Value) AS INTEGER)         AS Liquidity
                    FROM
                        datetimeIntervalList
                    LEFT JOIN AllChannelSessions
                        ON datetimeIntervalList.StartDate <= AllChannelSessions.EndDate AND AllChannelSessions.StartDate <= datetimeIntervalList.EndDate
                    
                    WHERE
                        datetimeIntervalList.StartDate <> 0 AND 
                        AllChannelSessions.short_channel_id IS NOT NULL
                    GROUP BY datetimeIntervalList.StartDate
                )
                
                INSERT OR REPLACE INTO _CACHED_Chart_TotalLiquidity
                SELECT LiquidityChartData.Date, LiquidityChartData.Liquidity FROM LiquidityChartData
            '''
            print(query)
            conn.execute(query, [(timeblocksize+1)*(backtrack+1), '2018-01-01', '2023-12-31', '2018-01-01' ])
            return  Response('Done', mimetype='application/json')
        




        elif(dataset == 'distributionliquidity'):
            conn.execute(' DELETE FROM _CACHED_Chart_DistributionLiquidity ')
            conn.commit()

            topEntitiesCount = 50

            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    for day in ['01']:
                        dateToCheck = f'{year}-{str(month).zfill(2)}-{day}'
                        print(dateToCheck)

                        dateToCheckRounded = f'{year}-{str(month).zfill(2)}-01'
                        conn.execute(f'''
                            -- Both Small Players
                            WITH OthersChannels AS
                            (
                                SELECT
                                    EntityName          AS EntityName,
                                    SUM(Value)          AS Value
                                FROM
                                (
                                    SELECT
                                        EntityName1 AS EntityName,
                                        ShortChannelID,
                                        Value
                                    FROM
                                        _VIEW_GetAllChannels
                                    WHERE
                                        StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                        EntityName1 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount}) AND
                                        EntityName2 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})

                                    UNION ALL
                                    
                                    SELECT
                                        EntityName2 AS EntityName,
                                        ShortChannelID,
                                        Value
                                    FROM
                                        _VIEW_GetAllChannels
                                    WHERE
                                        StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                        EntityName1 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount}) AND
                                        EntityName2 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})
                                        
                                )
                            ),
                            
                            -- One Big Player and Other is Small
                            OthersAndTopChannels AS
                            (
                                SELECT
                                    EntityName      AS EntityName,
                                    SUM(Value)      AS Value
                                FROM
                                (
                                    SELECT
                                        EntityName,
                                        ShortChannelID,
                                        Value
                                    FROM
                                    (
                                        SELECT
                                            EntityName1         AS EntityName,
                                            ShortChannelID      AS ShortChannelID,
                                            Value               AS Value
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount}) AND
                                            EntityName2 IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})
                                            
                                        UNION ALL
                                        
                                        SELECT
                                            EntityName2         AS EntityName,
                                            ShortChannelID      AS ShortChannelID,
                                            Value               AS Value
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount}) AND
                                            EntityName2 NOT IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})
                                    )
                                )
                            ),
                            
                            -- TOP Players List Channels with Everybody
                            TopPlayersChannels AS
                            (
                                SELECT
                                    EntityName      AS EntityName,
                                    SUM(Value)      AS Value
                                FROM
                                (
                                    SELECT
                                        EntityName      AS EntityName,
                                        ShortChannelID  AS ShortChannelID,
                                        SUM(Value)      AS Value
                                    FROM
                                    (
                                        SELECT
                                            EntityName1     AS EntityName,
                                            ShortChannelID  AS ShortChannelID,
                                            Value           AS Value
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})

                                        UNION ALL

                                        SELECT 
                                            EntityName2         AS EntityName,
                                            ShortChannelID      AS ShortChannelID,
                                            Value               AS Value
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName2 IN (SELECT Name FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY Liquidity DESC LIMIT {topEntitiesCount})

                                    )
                                    GROUP BY EntityName, ShortChannelID
                                    
                                )
                                GROUP BY EntityName
                            ),
                            
                            LiquidityOfEntitiesTable AS
                            (
                                SELECT
                                    EntityName          AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    IFNULL(Value, 0.0)               AS Liquidity
                                FROM
                                    TopPlayersChannels

                                UNION ALL
                                
                                SELECT
                                    'Kiti_ir_TOP'       AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    IFNULL(Value, 0.0)               AS Liquidity
                                FROM
                                    OthersAndTopChannels
                                    
                                UNION ALL
                                
                                SELECT
                                    'Kiti'              AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    IFNULL(Value, 0.0)               AS Liquidity
                                FROM
                                    OthersChannels
                            )

                            INSERT OR REPLACE INTO _CACHED_Chart_DistributionLiquidity
                            SELECT Date, EntityName, Liquidity FROM LiquidityOfEntitiesTable;
                        ''')         
            conn.execute(" UPDATE _CACHED_Chart_DistributionChannel SET Name = '<EMPTY>' WHERE Name = '' ")
            return  Response('Done', mimetype='application/json')

        elif(dataset == 'distributionchannel10pcnt'):
            conn.execute(' DELETE FROM _CACHED_Chart_DistributionChannel10Pcnt ')
            conn.commit()
            conn.execute(f'''
                WITH TopPlayersChannelCount AS (
                    SELECT
                        "Date" AS "Date",
                        SUM(ChannelCount) AS TopChannelCount
                    FROM
                        _CACHED_TopChannelCountEntitiesByTime_10Pcnt
                    GROUP BY "Date"
                ),
                            
                GetTable AS (
                    SELECT 
                        _CACHED_Chart_ChannelCount.Date		AS "Date",
                        Value * 2 - TopChannelCount         AS LowerChannelCount,
                        TopChannelCount		                AS TopChannelCount
                    FROM
                        _CACHED_Chart_ChannelCount
                    LEFT JOIN TopPlayersChannelCount
                        ON TopPlayersChannelCount.Date = _CACHED_Chart_ChannelCount.Date
                    WHERE
                        TopPlayersChannelCount.Date IS NOT NULL
                ),
                
                GetMergedTable AS (
                    SELECT Date, 'TOP10Pcnt' AS Name, TopChannelCount FROM GetTable
                    
                    UNION ALL
                    
                    SELECT Date, 'Lower90Pcnt' AS Name, LowerChannelCount FROM GetTable
                )
                
                INSERT INTO _CACHED_Chart_DistributionChannel10Pcnt
                SELECT * FROM GetMergedTable
            ''')
            conn.commit()
            return  Response('Done', mimetype='application/json')

        elif(dataset == 'distributionliquidity10pcnt'):
            conn.execute(' DELETE FROM _CACHED_Chart_DistributionLiquidity10Pcnt ')
            conn.commit()
            conn.execute(f'''
                WITH TopPlayersLiquidity AS (
                    SELECT
                        "Date" AS "Date",
                        SUM(Liquidity) AS TopLiquidity
                    FROM
                        _CACHED_TopLiquidityEntitiesByTime_10Pcnt
                    GROUP BY "Date"
                ),
                            
                GetTable AS (
                    SELECT 
                        _CACHED_Chart_TotalLiquidity.Date		AS "Date",
                        Value * 2 - TopLiquidity 			    AS LowerLiquidity,
                        TopLiquidity                            AS TopLiquidity
                    FROM
                        _CACHED_Chart_TotalLiquidity
                    LEFT JOIN TopPlayersLiquidity
                        ON TopPlayersLiquidity.Date = _CACHED_Chart_TotalLiquidity.Date
                    WHERE
                        TopPlayersLiquidity.Date IS NOT NULL
                ),
                
                GetMergedTable AS (
                    SELECT Date, 'TOP10Pcnt' AS Name, CAST(TopLiquidity AS INTEGER) FROM GetTable
                    
                    UNION ALL
                    
                    SELECT Date, 'Lower90Pcnt' AS Name, LowerLiquidity FROM GetTable
                )
                
                INSERT INTO _CACHED_Chart_DistributionLiquidity10Pcnt
                SELECT * FROM GetMergedTable
            ''')
            conn.commit()
            return  Response('Done', mimetype='application/json')

        elif(dataset == 'distributionchannels'):
            topEntitiesCount = 50

            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    for day in ['01']:
                        dateToCheck = f'{year}-{str(month).zfill(2)}-{day}'
                        print(dateToCheck)

                        dateToCheckRounded = f'{year}-{str(month).zfill(2)}-01'
                        conn.execute(f'''
                            -- Both Small Players
                            WITH OthersChannels AS
                            (
                                SELECT
                                    EntityName          AS EntityName,
                                    COUNT(*)            AS ChannelCount
                                FROM
                                (
                                    SELECT
                                        EntityName1 AS EntityName,
                                        ShortChannelID
                                    FROM
                                        _VIEW_GetAllChannels
                                    WHERE
                                        StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                        EntityName1 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount}) AND
                                        EntityName2 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})

                                    UNION ALL
                                    
                                    SELECT
                                        EntityName2 AS EntityName,
                                        ShortChannelID
                                    FROM
                                        _VIEW_GetAllChannels
                                    WHERE
                                        StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                        EntityName1 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount}) AND
                                        EntityName2 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})
                                        
                                )
                            ),

                            -- One Big Player and Other is Small
                            OthersAndTopChannels AS
                            (
                                SELECT
                                    EntityName      AS EntityName,
                                    COUNT(*)        AS ChannelCount
                                FROM
                                (
                                    SELECT
                                        EntityName,
                                        ShortChannelID
                                    FROM
                                    (
                                        SELECT
                                            EntityName1         AS EntityName,
                                            ShortChannelID      AS ShortChannelID
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount}) AND
                                            EntityName2 IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})
                                            
                                        UNION ALL
                                        
                                        SELECT
                                            EntityName2         AS EntityName,
                                            ShortChannelID      AS ShortChannelID
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount}) AND
                                            EntityName2 NOT IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})
                                    )
                                )
                            ),

                            -- TOP Players List Channels with Everybody
                            TopPlayersChannels AS
                            (
                                SELECT
                                    EntityName      AS EntityName,
                                    COUNT(*)        AS ChannelCount
                                FROM
                                (
                                    SELECT
                                        EntityName      AS EntityName,
                                        ShortChannelID  AS ShortChannelID
                                    FROM
                                    (
                                        SELECT
                                            EntityName1 AS EntityName,
                                            ShortChannelID
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName1 IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})

                                        UNION ALL

                                        SELECT
                                            EntityName2 AS EntityName,
                                            ShortChannelID
                                        FROM
                                            _VIEW_GetAllChannels
                                        WHERE
                                            StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' AND
                                            EntityName2 IN (SELECT Name FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = '{dateToCheckRounded}' ORDER BY ChannelCount DESC LIMIT {topEntitiesCount})

                                    )
                                    GROUP BY ShortChannelID
                                    
                                )
                                GROUP BY EntityName
                            ),
                            
                            ChannelCountOfEntitiesTable AS
                            (
                                SELECT
                                    EntityName          AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    ChannelCount        AS ChannelCount
                                FROM
                                    TopPlayersChannels

                                UNION ALL
                                
                                SELECT
                                    'Kiti_ir_TOP'       AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    ChannelCount        AS ChannelCount
                                FROM
                                    OthersAndTopChannels
                                    
                                UNION ALL
                                
                                SELECT
                                    'Kiti'              AS EntityName,
                                    '{dateToCheck}'     AS Date,
                                    ChannelCount        AS ChannelCount
                                FROM
                                    OthersChannels
                            )

                            INSERT OR REPLACE INTO _CACHED_Chart_DistributionChannel
                            SELECT Date, EntityName, ChannelCount FROM ChannelCountOfEntitiesTable;
                        ''')         
            conn.execute(" UPDATE _CACHED_Chart_DistributionChannel SET Name = '<EMPTY>' WHERE Name = '' ")
            return  Response('Done', mimetype='application/json')

        elif(dataset == 'liquidityconnections'):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    if(dateToCheck < '2018-12-01' or dateToCheck >= '2023-10-01'):
                        continue

                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetNodeAliases AS (
                            SELECT
                                NodeID,
                                alias
                            FROM Lightning_NodeAliases
                            GROUP BY NodeID
                        ),
                        GetTopPlayersAtTheTime AS (
                            SELECT 
                                Channels.NodeID             AS NodeID,
                                SUM(Value)                  AS TotalValue,
                                Lightning_Entities.Name     AS EntityName
                            FROM (
                                SELECT
                                    node_id_1 AS NodeID,
                                    short_channel_id AS ShortChannelID
                                FROM
                                    LNResearch_20230924_ChannelAnnouncement
                                    
                                UNION ALL

                                SELECT
                                    node_id_2 AS NodeID,
                                    short_channel_id AS ShortChannelID
                                FROM
                                    LNResearch_20230924_ChannelAnnouncement
                            ) AS Channels
                            LEFT JOIN Blockchain_Transactions
                                ON Channels.ShortChannelID = Blockchain_Transactions.ShortChannelID
                            LEFT JOIN GetNodeAliases
                                ON GetNodeAliases.NodeID = Channels.NodeID
                            LEFT JOIN Lightning_Entities
                                ON GetNodeAliases.Alias = Lightning_Entities.Alias
                            LEFT JOIN Blockchain_Blocks AS FundingBlock
                                ON FundingBlock.BlockIndex = Blockchain_Transactions.FundingBlockIndex
                            LEFT JOIN Blockchain_Blocks AS SpendingBlock
                                ON SpendingBlock.BlockIndex = Blockchain_Transactions.SpendingBlockIndex
                            WHERE 
                            FundingBlock.Date <= '{dateToCheck}' AND SpendingBlock.Date >= '{dateToCheck}'
                            GROUP BY Lightning_Entities.Name
                            ORDER BY TotalValue DESC
                            LIMIT 50
                        ),

                        GetConnectionsOfTopPlayers AS (
                            SELECT
                                IIF(NodeEntity1.Name < NodeEntity2.Name,NodeEntity1.Name, NodeEntity2.Name)     AS Entity1,
                                IIF(NodeEntity1.Name > NodeEntity2.Name,NodeEntity1.Name, NodeEntity2.Name)     AS Entity2,
                                CAST( SUM(Blockchain_Transactions.Value) AS INTEGER )	 					    AS Value
                            FROM
                                LNResearch_20230924_ChannelAnnouncement

                            -- Find  Entity 1
                            LEFT JOIN Lightning_NodeAliases AS NodeAlias1
                                ON LNResearch_20230924_ChannelAnnouncement.node_id_1 = NodeAlias1.NodeID
                            LEFT JOIN Lightning_Entities AS NodeEntity1
                                ON NodeAlias1.Alias = NodeEntity1.Alias
                                
                            -- Find  Entity 2
                            LEFT JOIN Lightning_NodeAliases AS NodeAlias2
                                ON LNResearch_20230924_ChannelAnnouncement.node_id_2 = NodeAlias2.NodeID
                            LEFT JOIN Lightning_Entities AS NodeEntity2
                                ON NodeAlias2.Alias = NodeEntity2.Alias

                            -- Find Channel Transaction
                            LEFT JOIN Blockchain_Transactions
                                ON Blockchain_Transactions.ShortChannelID = LNResearch_20230924_ChannelAnnouncement.short_channel_id
                            LEFT JOIN Blockchain_Blocks AS FundingBlock
                                ON FundingBlock.BlockIndex = Blockchain_Transactions.FundingBlockIndex
                            LEFT JOIN Blockchain_Blocks AS SpendingBlock
                                ON SpendingBlock.BlockIndex = Blockchain_Transactions.SpendingBlockIndex
                            WHERE
                                FundingBlock.Date <= '{dateToCheck}' AND SpendingBlock.Date >= '{dateToCheck}' AND
                                Entity1 <> Entity2 AND
                                Entity1 IN ( SELECT EntityName FROM GetTopPlayersAtTheTime) AND
                                Entity2 IN ( SELECT EntityName FROM GetTopPlayersAtTheTime)
                            GROUP BY Entity1, Entity2
                            ORDER BY Value DESC
                        )

                        SELECT Entity1, Entity2, Value FROM GetConnectionsOfTopPlayers WHERE Value > 0
                    ''')
                    
                    for sqlLine in sqlFetchTopPlayerConnections.fetchall():
                        conn.execute(' INSERT OR REPLACE INTO _CACHED_Chart_LiquidityConnections VALUES (?,?,?,?)  ', [ dateToCheck, sqlLine[0], sqlLine[1], sqlLine[2] ])
                        conn.commit()




        elif(dataset.lower() == 'TopChannelCountEntitiesByTime'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    conn.execute(' DELETE FROM _CACHED_TopChannelCountEntitiesByTime WHERE Date = ?  ', [ dateToCheck ])
                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetTopPlayersAtTheTimeByChannelCount AS (
                            SELECT
                                Entity      AS Entity,
                                Count(*)    AS ChannelCount
                            FROM
                            (
                                SELECT
                                    EntityName1 AS Entity
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    EntityName2 AS Entity
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                            )
                            GROUP BY Entity
                            ORDER BY ChannelCount DESC
                            LIMIT 50
                            
                        )

                        INSERT INTO _CACHED_TopChannelCountEntitiesByTime
                        SELECT '{dateToCheck}', Entity, ChannelCount FROM GetTopPlayersAtTheTimeByChannelCount WHERE ChannelCount > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')




        elif(dataset.lower() == 'TotalChannelCountNodesByTime'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetNodesAtTheTimeByChannelCount AS (
                            SELECT
                                NodeID      AS NodeID,
                                Count(*)    AS ChannelCount
                            FROM
                            (
                                SELECT
                                    NodeID1 AS NodeID
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    NodeID2 AS NodeID
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                            )
                            GROUP BY NodeID
                            ORDER BY ChannelCount DESC
                        )

                        INSERT OR REPLACE INTO _CACHED_TotalChannelCountNodesByTime
                        SELECT '{dateToCheck}', NodeID, ChannelCount FROM GetNodesAtTheTimeByChannelCount WHERE ChannelCount > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')




        elif(dataset.lower() == 'TotalLiquidityNodesByTime'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    momentOfTimeToCheck = f'{year}-{str(month).zfill(2)}-01T00:00:00'
                    print(dateToCheck)

                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetNodesAtTheTimeByLiquidity AS (
                            SELECT 
                                NodeID      AS NodeID,
                                SUM(Value)  AS Liquidity
                            FROM 
                            (
                                SELECT 
                                    NodeID1 AS NodeID,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{momentOfTimeToCheck}' AND EndDate >= '{momentOfTimeToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    NodeID2 AS NodeID,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{momentOfTimeToCheck}' AND EndDate >= '{momentOfTimeToCheck}' 
                            )
                            GROUP BY NodeID
                            ORDER BY Liquidity DESC
                        )

                        INSERT OR REPLACE INTO _CACHED_TotalLiquidityNodesByTime
                        SELECT '{dateToCheck}', NodeID, Liquidity FROM GetNodesAtTheTimeByLiquidity WHERE Liquidity > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'GiniLiquidity'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    sqlFetchData = conn.execute('''
                        SELECT
                            Liquidity
                        FROM
                            _CACHED_TotalLiquidityNodesByTime
                        WHERE
                            Date = ?
                        ORDER BY Liquidity ASC
                    ''', [dateToCheck])
                    rows = sqlFetchData.fetchall()

                    rowCount = len(rows)
                    if rowCount == 0:
                        print(f"No data available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    total_liquidity = sum([row[0] for row in rows])
                    if total_liquidity == 0:
                        print(f"No liquidity available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    gini_sum = 0
                    for i, row in enumerate(rows, 1):
                        rank = 2 * i - rowCount - 1
                        value = row[0]
                        gini_sum += rank * value
                    gini = gini_sum / (rowCount * total_liquidity)

                    conn.execute(" INSERT OR REPLACE INTO _CACHED_GiniLiquidity VALUES (?,?)", [dateToCheck, gini])
                    conn.commit()
            return Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'GiniLiquidityByEntities'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    sqlFetchData = conn.execute('''
                        SELECT
                            Liquidity
                        FROM
                            _CACHED_TotalLiquidityNodesByTime
                        WHERE
                            Date = ?
                        ORDER BY Liquidity ASC
                    ''', [dateToCheck])
                    rows = sqlFetchData.fetchall()

                    rowCount = len(rows)
                    if rowCount == 0:
                        print(f"No data available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    total_liquidity = sum([row[0] for row in rows])
                    if total_liquidity == 0:
                        print(f"No liquidity available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    gini_sum = 0
                    for i, row in enumerate(rows, 1):
                        rank = 2 * i - rowCount - 1
                        value = row[0]
                        gini_sum += rank * value
                    gini = gini_sum / (rowCount * total_liquidity)

                    conn.execute(" INSERT OR REPLACE INTO _CACHED_GiniLiquidityByEntities VALUES (?,?)", [dateToCheck, gini])
                    conn.commit()
            return Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'GiniChannelCount'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    sqlFetchData = conn.execute('''
                        SELECT
                            ChannelCount
                        FROM
                            _CACHED_TotalChannelCountNodesByTime
                        WHERE
                            Date = ?
                        ORDER BY ChannelCount ASC
                    ''', [dateToCheck])
                    rows = sqlFetchData.fetchall()

                    rowCount = len(rows)
                    if rowCount == 0:
                        print(f"No data available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    total_channelCount = sum([row[0] for row in rows])
                    if total_channelCount == 0:
                        print(f"No channel count available for {dateToCheck}. Skipping Gini calculation.")
                        continue

                    gini_sum = 0
                    for i, row in enumerate(rows, 1):
                        rank = 2 * i - rowCount - 1
                        value = row[0]
                        gini_sum += rank * value
                    gini = gini_sum / (rowCount * total_channelCount)

                    conn.execute(" INSERT OR REPLACE INTO _CACHED_GiniChannelCount VALUES (?,?)", [dateToCheck, gini])
                    conn.commit()
            return Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'TopChannelCountEntitiesByTime_10Pcnt'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    conn.execute(' DELETE FROM _CACHED_TopChannelCountEntitiesByTime_10Pcnt WHERE Date = ?  ', [ dateToCheck ])
                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetTopPlayersAtTheTimeByChannelCount AS (
                            SELECT
                                Entity      AS Entity,
                                Count(*)    AS ChannelCount
                            FROM
                            (
                                SELECT
                                    EntityName1 AS Entity
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    EntityName2 AS Entity
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                            )
                            GROUP BY Entity
                            ORDER BY ChannelCount DESC
                        ),

                        LimitQuery AS (
                            SELECT CAST(COUNT(*) * 0.10 AS INTEGER) AS limit_value FROM GetTopPlayersAtTheTimeByChannelCount
                        ),

                        GetTopPlayersAtTheTimeByChannelCount_10Pcnt AS (
                            SELECT
                                Entity          AS Entity,
                                ChannelCount    AS ChannelCount
                            FROM
                                GetTopPlayersAtTheTimeByChannelCount
                            LIMIT (SELECT limit_value FROM LimitQuery)
                        )

                        INSERT INTO _CACHED_TopChannelCountEntitiesByTime_10Pcnt
                        SELECT '{dateToCheck}', Entity, ChannelCount FROM GetTopPlayersAtTheTimeByChannelCount_10Pcnt WHERE ChannelCount > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'TopLiquidityEntitiesByTime_10Pcnt'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    conn.execute(' DELETE FROM _CACHED_TopLiquidityEntitiesByTime_10Pcnt WHERE Date = ?  ', [ dateToCheck ])
                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetTopPlayersAtTheTimeByLiquidity AS (
                            SELECT 
                                Entity      AS Entity,
                                SUM(Value)  AS Liquidity
                            FROM 
                            (
                                SELECT 
                                    EntityName1 AS Entity,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    EntityName2 AS Entity,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                            )
                            GROUP BY Entity
                            ORDER BY Liquidity DESC
                        ),

                        LimitQuery AS (
                            SELECT CAST(COUNT(*) * 0.10 AS INTEGER) AS limit_value FROM GetTopPlayersAtTheTimeByLiquidity
                        ),

                        GetTopPlayersAtTheTimeByLiquidity_10Pcnt AS (
                            SELECT
                                Entity          AS Entity,
                                Liquidity       AS Liquidity
                            FROM
                                GetTopPlayersAtTheTimeByLiquidity
                            LIMIT (SELECT limit_value FROM LimitQuery)
                        )

                        INSERT INTO _CACHED_TopLiquidityEntitiesByTime_10Pcnt
                        SELECT '{dateToCheck}', Entity, Liquidity FROM GetTopPlayersAtTheTimeByLiquidity_10Pcnt WHERE Liquidity > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')



        elif(dataset.lower() == 'TopLiquidityEntitiesByTime'.lower()):
            for year in range(2018, 2023+1):
                for month in range(1, 12+1):
                    dateToCheck = f'{year}-{str(month).zfill(2)}-01'
                    print(dateToCheck)

                    conn.execute(' DELETE FROM _CACHED_TopLiquidityEntitiesByTime WHERE Date = ?  ', [ dateToCheck ])
                    sqlFetchTopPlayerConnections = conn.execute(f'''
                        WITH GetTopPlayersAtTheTimeByLiquidity AS (
                            SELECT 
                                Entity      AS Entity,
                                SUM(Value)  AS Liquidity
                            FROM 
                            (
                                SELECT 
                                    EntityName1 AS Entity,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                                    
                                UNION ALL

                                SELECT 
                                    EntityName2 AS Entity,
                                    Value
                                FROM
                                    _VIEW_GetAllChannels
                                WHERE
                                    StartDate <= '{dateToCheck}' AND EndDate >= '{dateToCheck}' 
                            )
                            GROUP BY Entity
                            ORDER BY Liquidity DESC
                            LIMIT 50
                            
                        )

                        INSERT INTO _CACHED_TopLiquidityEntitiesByTime
                        SELECT '{dateToCheck}', Entity, Liquidity FROM GetTopPlayersAtTheTimeByLiquidity WHERE Liquidity > 0
                    ''')
                    conn.commit()
            return  Response('Done', mimetype='application/json')

        return  Response('{}', mimetype='application/json')





@app.route('/api/chart/<string:dataset>/<string:selectedTime>', methods=['GET'])
@app.route('/api/chart/<string:dataset>', methods=['GET'])
def charts_HTTPGET(dataset, selectedTime=''):
    with get_db_connection() as conn:
        if(dataset == 'channelcount'):
            query = f'''
                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'Date',       Date,
                                'KanaluSk',   Value
                            )
                        )
                    )
                FROM
                    _CACHED_Chart_ChannelCount
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')
        
        elif(dataset == 'nodecount'):
            query = f'''
                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'Date',     Date,
                                'MazguSk',  Value
                            )
                        )
                    )
                FROM
                    _CACHED_Chart_NodeCount
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')
        
        elif(dataset == 'totalliquidity'):
            query = f'''
                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'Date',     Date,
                                'BTC',  Value
                            )
                        )
                    )
                FROM
                    _CACHED_Chart_TotalLiquidity
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')
        
        elif(dataset == 'distributionliquidity'):
            distinct_names = conn.execute("SELECT DISTINCT Name FROM _CACHED_Chart_DistributionLiquidity").fetchall()

            case_clauses = []
            
            for name_tuple in distinct_names:
                name = name_tuple[0]
                case_clauses.append(f'''IFNULL(MAX(CASE WHEN Name = '{name}' THEN Liquidity ELSE NULL END), 0) AS "{name}"''')

            query = f'''
                SELECT 
                    Date,
                    {', '.join(case_clauses)}
                FROM _CACHED_Chart_DistributionLiquidity
                WHERE Date <= '2023-09-24'
                GROUP BY Date
                ORDER BY Date;
            '''
            sqlFetchData = conn.execute(query).fetchall()

            result = []
            for row in sqlFetchData:
                date_value = row[0]
                data = {"Date": date_value}
                for i, name_tuple in enumerate(distinct_names, start=1):
                    name = name_tuple[0]
                    data[name] = row[i]
                result.append(data)

            return Response(json.dumps(result, indent=4), mimetype='application/json')
        
        elif(dataset == 'distributionliquidity10pcnt'):
            distinct_names = conn.execute("SELECT DISTINCT Name FROM _CACHED_Chart_DistributionLiquidity10Pcnt").fetchall()

            case_clauses = []
            
            for name_tuple in distinct_names:
                name = name_tuple[0]
                case_clauses.append(f'''IFNULL(MAX(CASE WHEN Name = '{name}' THEN Liquidity ELSE NULL END), 0) AS "{name}"''')

            query = f'''
                SELECT 
                    Date,
                    {', '.join(case_clauses)}
                FROM _CACHED_Chart_DistributionLiquidity10Pcnt
                WHERE Date <= '2023-09-24'
                GROUP BY Date
                ORDER BY Date;
            '''
            sqlFetchData = conn.execute(query).fetchall()

            result = []
            for row in sqlFetchData:
                date_value = row[0]
                data = {"Date": date_value}
                for i, name_tuple in enumerate(distinct_names, start=1):
                    name = name_tuple[0]
                    data[name] = row[i]
                result.append(data)

            return Response(json.dumps(result, indent=4), mimetype='application/json')
        
        elif(dataset == 'distributionchannel10pcnt'):
            distinct_names = conn.execute("SELECT DISTINCT Name FROM _CACHED_Chart_DistributionChannel10Pcnt").fetchall()

            case_clauses = []
            
            for name_tuple in distinct_names:
                name = name_tuple[0]
                case_clauses.append(f'''IFNULL(MAX(CASE WHEN Name = '{name}' THEN ChannelCount ELSE NULL END), 0) AS "{name}"''')

            query = f'''
                SELECT 
                    Date,
                    {', '.join(case_clauses)}
                FROM _CACHED_Chart_DistributionChannel10Pcnt
                WHERE Date <= '2023-09-24'
                GROUP BY Date
                ORDER BY Date;
            '''
            sqlFetchData = conn.execute(query).fetchall()

            result = []
            for row in sqlFetchData:
                date_value = row[0]
                data = {"Date": date_value}
                for i, name_tuple in enumerate(distinct_names, start=1):
                    name = name_tuple[0]
                    data[name] = row[i]
                result.append(data)

            return Response(json.dumps(result, indent=4), mimetype='application/json')
        
        elif dataset == 'distributionchannel':
            distinct_names = conn.execute("SELECT DISTINCT Name FROM _CACHED_Chart_DistributionChannel").fetchall()

            case_clauses = []
            
            for name_tuple in distinct_names:
                name = name_tuple[0]
                case_clauses.append(f'''IFNULL(MAX(CASE WHEN Name = '{name}' THEN ChannelCount ELSE NULL END), 0) AS "{name}"''')

            query = f'''
                SELECT 
                    Date,
                    {', '.join(case_clauses)}
                FROM _CACHED_Chart_DistributionChannel
                WHERE Date <= '2023-09-24'
                GROUP BY Date
                ORDER BY Date;
            '''
            sqlFetchData = conn.execute(query).fetchall()

            result = []
            for row in sqlFetchData:
                date_value = row[0]
                data = {"Date": date_value}
                for i, name_tuple in enumerate(distinct_names, start=1):
                    name = name_tuple[0]
                    data[name] = row[i]
                result.append(data)

            return Response(json.dumps(result, indent=4), mimetype='application/json')

        elif(dataset == 'liquidityconnections'):
            sqlFetchData = conn.execute('''
               SELECT
                    json_group_array(
                        json_object(
                            'date', Date,
                            'entity1', Entity1,
                            'entityGroup1', (SELECT _rowid_ FROM Lightning_Entities WHERE Name = Entity1),
                            'entity2', Entity2,
                            'entityGroup2', (SELECT _rowid_ FROM Lightning_Entities WHERE Name = Entity2),
                            'value', Value
                        )
                    )
                FROM
                    _CACHED_Chart_LiquidityConnections
            ''')
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')

        elif(dataset == 'ginichannelcount'):
            query = f'''
                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'Date',     Date,
                                'Gini',     ROUND(Gini, 3)
                            )
                        )
                    )
                FROM
                    _CACHED_GiniChannelCount
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')
        
        elif(dataset == 'giniliquidity'):
            query = f'''
                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'Date',     Date,
                                'Gini',     ROUND(Gini, 3)
                            )
                        )
                    )
                FROM
                    _CACHED_GiniLiquidity
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')

        elif(dataset == 'lorenzliquiditycurvebynodes'):
            query = f'''
                WITH LiquidityData AS (
                    SELECT
                        Liquidity,
                        NTILE(100) OVER (ORDER BY Liquidity ASC) AS Percentile,
                        SUM(Liquidity) OVER () AS TotalLiquidity
                    FROM _CACHED_TotalLiquidityNodesByTime
                    WHERE Date = ? --AND Liquidity > 1.0
                ),
                PercentileAggregates AS (
                    SELECT
                        Percentile,
                        SUM(Liquidity) AS SumLiquidity,
                        SUM(SUM(Liquidity)) OVER (ORDER BY Percentile) AS CumulativeLiquidity,
                        MAX(TotalLiquidity) OVER () AS TotalLiquidity
                    FROM LiquidityData
                    GROUP BY Percentile
                ),
                GetTable AS (
                    SELECT
                        Percentile,
                        CumulativeLiquidity,
                        ROUND((CumulativeLiquidity * 100.0 / TotalLiquidity), 1) AS CumulativePercentageOfLiquidity
                    FROM PercentileAggregates
                    ORDER BY Percentile
                )

                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'x',     Percentile,
                                'y',     CumulativePercentageOfLiquidity
                            )
                        )
                    )
                FROM
                    GetTable
            '''
            sqlFetchData = conn.execute(query, [selectedTime])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')

        elif(dataset == 'lorenzchannelcountcurvebynodes'):
            query = f'''
                WITH ChannelCountData AS (
                    SELECT
                        ChannelCount,
                        NTILE(100) OVER (ORDER BY ChannelCount ASC) AS Percentile,
                        SUM(ChannelCount) OVER () AS TotalChannelCount
                    FROM _CACHED_TotalChannelCountNodesByTime
                    WHERE Date = ?
                ),
                PercentileAggregates AS (
                    SELECT
                        Percentile,
                        SUM(ChannelCount) AS SumChannelCount,
                        SUM(SUM(ChannelCount)) OVER (ORDER BY Percentile) AS CumulativeChannelCount,
                        MAX(TotalChannelCount) OVER () AS TotalChannelCount
                    FROM ChannelCountData
                    GROUP BY Percentile
                ),
                GetTable AS (
                    SELECT
                        Percentile,
                        CumulativeChannelCount,
                        ROUND((CumulativeChannelCount * 100.0 / TotalChannelCount), 1) AS CumulativePercentageOfChannelCount
                    FROM PercentileAggregates
                    ORDER BY Percentile
                )

                SELECT
                    json_object
                    (
                        'chartdata', json_group_array
                        (
                            json_object
                            (
                                'x', Percentile,
                                'y', CumulativePercentageOfChannelCount
                            )
                        )
                    )
                FROM
                    GetTable
            '''
            sqlFetchData = conn.execute(query, [selectedTime])
            return  Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')

        return  Response('{}', mimetype='application/json')

@app.route('/api/generate/chart/<string:dataset>', methods=['GET'])
def generateCharts_HTTPGET(dataset):
    dayOfyear = '-06-01'
    with get_db_connection() as conn:
        if(dataset == 'ginichannelcountbynodes' or dataset == "giniliquiditybynodes"):
            plt.figure(figsize=(4, 6), linewidth=3)

            query = ''
            if(dataset == 'ginichannelcountbynodes'):
                query = f'''
                    SELECT
                        Date, ROUND(Gini, 3)
                    FROM
                        _CACHED_GiniChannelCount
                    WHERE
                        Date <= '2023-09-24'
                '''
            elif(dataset == 'giniliquiditybynodes'):
                query = f'''
                    SELECT
                        Date, ROUND(Gini, 3)
                    FROM
                        _CACHED_GiniLiquidity
                    WHERE
                        Date <= '2023-09-24'
                '''
            sqlFetchData = conn.execute(query, [])
            data = sqlFetchData.fetchall()

            dates = [datetime.strptime(line[0], '%Y-%m-%d') for line in data]
            gini = [line[1] for line in data]
            plt.plot(dates, gini, label=f"Gini Coefficient")

            # Customize x-axis
            ax = plt.gca()
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.set_ylim(ymin=0.79, ymax=1)
            xticks = [date for date in dates if date.strftime('-%m-%d') == dayOfyear]
            ax.set_xticks(xticks)

            plt.gcf().autofmt_xdate()

            title_map = {
                'ginichannelcountbynodes': 'Gini coefficient of degree\ncentrality (BLN Nodes)',
                'giniliquiditybynodes': 'Gini coefficient of weighted degree\ncentrality (BLN Nodes)'
            }
            plt.title(title_map.get(dataset, 'Gini Coefficient'), fontsize="15")
            plt.xlabel('Time', fontsize="15")
            plt.ylabel('Gini Coefficient', fontsize="15")
            plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="15")
            plt.grid(True)

            plt.tight_layout()

            virtual_file = BytesIO()
            plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
            virtual_file.seek(0)

            response = send_file(virtual_file, mimetype='image/png')
            response.headers['Content-Disposition'] = 'inline'
            return response

        elif(dataset == 'lorenzexample'):
            plt.figure(figsize=(10, 6), linewidth=3)

            ax = plt.gca()
            ax.set_xlim(xmin=0, xmax=100)
            ax.set_ylim(ymin=0, ymax=100)
            ax.xaxis.tick_bottom()
            ax.yaxis.tick_left()
            ax.yaxis.set_label_position("left")

            ax.set_xticklabels([f'{int(tick)}%' for tick in plt.gca().get_xticks()])
            ax.set_yticklabels([f'{int(tick)}%' for tick in plt.gca().get_yticks()])

            plt.plot([0, 100], [0, 100], 'k--')
            plt.text(50, 55, 'Perfect Equality Line', rotation=30, ha='center', va='center', fontsize="15")

            x_lorenz = np.linspace(0, 100, 100)
            y_lorenz = (x_lorenz / 100) ** 4 * 100
            plt.plot(x_lorenz, y_lorenz, label='Lorenz Curve', linewidth=3, color='black')

            plt.fill_between(x_lorenz, y_lorenz, x_lorenz, hatch='///\\\\\\', edgecolor='black', facecolor='white')
            plt.text(55, 35, 'Gini Coefficient', rotation=0, ha='center', va='center', fontsize=15, bbox=dict(facecolor='white', alpha=1))
            plt.text(85, 70, 'A', rotation=0, ha='center', va='center', fontsize=25, bbox=dict(facecolor='white', alpha=1))

            plt.fill_between(x_lorenz, y_lorenz, hatch='++', edgecolor='black', facecolor='white')
            plt.text(85, 25, 'B', rotation=0, ha='center', va='center', fontsize=25, bbox=dict(facecolor='white', alpha=1))

            plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="20")
            plt.grid(False)

            plt.tight_layout()

            virtual_file = BytesIO()
            plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
            virtual_file.seek(0)

            response = send_file(virtual_file, mimetype='image/png')
            response.headers['Content-Disposition'] = 'inline'
            return response

        elif(dataset == 'totalnodesbytime'):
            plt.figure(figsize=(10, 6), linewidth=3)
            query = f'''
                SELECT
                    Date, Value
                FROM
                    _CACHED_Chart_NodeCount
                WHERE
                    Date <= '2023-09-24'
            '''
            sqlFetchData = conn.execute(query, [])
            data = sqlFetchData.fetchall()

            dates = [datetime.strptime(line[0], '%Y-%m-%d') for line in data]
            nodecount = [line[1] for line in data]
            plt.plot(dates, nodecount, label=f"Node Count")

            ax = plt.gca()
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            xticks = [dates[0], dates[-1]] + [date for date in dates if date.strftime('%m-%d') == '03-01' and date.strftime('%Y-%m-%d') != '2018-03-01']
            ax.set_xticks(xticks)

            plt.gcf().autofmt_xdate()

            title_map = {
                'totalnodesbytime': 'BLN node count throughout time',
            }
            plt.title(title_map.get(dataset), fontsize="15")
            plt.xlabel('Time', fontsize="15")
            plt.ylabel('BLN Node Count', fontsize="15")
            plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="15")
            plt.grid(True)

            plt.tight_layout()

            virtual_file = BytesIO()
            plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
            virtual_file.seek(0)

            response = send_file(virtual_file, mimetype='image/png')
            response.headers['Content-Disposition'] = 'inline'
            return response

        elif(dataset == 'lorenzbychannelcountsbynodes' or dataset == 'lorenzbyliquiditybynodes'):
            plt.figure(figsize=(6, 6), linewidth=3)
            for i, year in enumerate(range(2018, 2024)):
                currentFocusedDate = str(year) + dayOfyear
                query = ''
                if(dataset == 'lorenzbychannelcountsbynodes'):
                    query = f'''
                        WITH ChannelCountData AS (
                            SELECT
                                ChannelCount,
                                NTILE(100) OVER (ORDER BY ChannelCount ASC) AS Percentile,
                                SUM(ChannelCount) OVER () AS TotalChannelCount
                            FROM _CACHED_TotalChannelCountNodesByTime
                            WHERE Date = ?
                        ),
                        PercentileAggregates AS (
                            SELECT
                                Percentile,
                                SUM(ChannelCount) AS SumChannelCount,
                                SUM(SUM(ChannelCount)) OVER (ORDER BY Percentile) AS CumulativeChannelCount,
                                MAX(TotalChannelCount) OVER () AS TotalChannelCount
                            FROM ChannelCountData
                            GROUP BY Percentile
                        ),
                        GetTable AS (
                            SELECT
                                Percentile,
                                CumulativeChannelCount,
                                ROUND((CumulativeChannelCount * 100.0 / TotalChannelCount), 1) AS CumulativePercentageOfChannelCount
                            FROM PercentileAggregates
                            ORDER BY Percentile
                        )

                        SELECT
                            Percentile, CumulativePercentageOfChannelCount
                        FROM
                            GetTable
                    '''
                elif(dataset == 'lorenzbyliquiditybynodes'):
                    query = f'''
                        WITH LiquidityData AS (
                            SELECT
                                Liquidity,
                                NTILE(100) OVER (ORDER BY Liquidity ASC) AS Percentile,
                                SUM(Liquidity) OVER () AS TotalLiquidity
                            FROM _CACHED_TotalLiquidityNodesByTime
                            WHERE Date = ? --AND Liquidity > 1.0
                        ),
                        PercentileAggregates AS (
                            SELECT
                                Percentile,
                                SUM(Liquidity) AS SumLiquidity,
                                SUM(SUM(Liquidity)) OVER (ORDER BY Percentile) AS CumulativeLiquidity,
                                MAX(TotalLiquidity) OVER () AS TotalLiquidity
                            FROM LiquidityData
                            GROUP BY Percentile
                        ),
                        GetTable AS (
                            SELECT
                                Percentile,
                                CumulativeLiquidity,
                                ROUND((CumulativeLiquidity * 100.0 / TotalLiquidity), 1) AS CumulativePercentageOfLiquidity
                            FROM PercentileAggregates
                            ORDER BY Percentile
                        )

                        SELECT
                            Percentile, CumulativePercentageOfLiquidity
                        FROM
                            GetTable
                    '''

                sqlFetchData = conn.execute(query, [currentFocusedDate])
                data = sqlFetchData.fetchall()

                percentiles = [line[0] for line in data]
                cumulativePercentages = [line[1] for line in data]

                def calculate_gini(percentiles, cumulativePercentages):
                    percentiles = [0] + percentiles + [100]
                    cumulativePercentages = [0] + cumulativePercentages + [100]
                    
                    gini = 1 - sum((percentiles[i] - percentiles[i-1]) * (cumulativePercentages[i] + cumulativePercentages[i-1]) for i in range(1, len(percentiles))) / 10000
                    
                    return gini
                
                currentDateGini = calculate_gini(percentiles, cumulativePercentages)
                currentDateGini = round(currentDateGini, 3)
                
                plt.plot(percentiles, cumulativePercentages, label=f"T{i+1}: {currentFocusedDate} (Gini: {currentDateGini})")

            ax = plt.gca()
            ax.set_xlim(xmin=0, xmax=100)
            ax.set_ylim(ymin=0, ymax=100)
            ax.xaxis.tick_bottom()
            ax.yaxis.tick_right()
            ax.set_xticklabels([f'{int(tick)}%' for tick in plt.gca().get_xticks()])
            ax.set_yticklabels([f'{int(tick)}%' for tick in plt.gca().get_yticks()])
            ax.yaxis.set_label_position("right")

            plt.plot([0, 100], [0, 100], 'k--')
            plt.text(50, 55, 'Perfect Equality Line', rotation=45, ha='center', va='center')

            if(dataset == 'lorenzbychannelcountsbynodes'):
                plt.title('Lorenz curves of degree centrality (BLN Nodes)', fontsize="15")
                plt.ylabel('Cumulative percentage of channels count', fontsize="15")
            elif(dataset == 'lorenzbyliquiditybynodes'):
                plt.title('Lorenz curves of weighted degree\ncentrality (BLN Nodes)', fontsize="15")
                plt.ylabel('Cumulative percentage of channels capacity', fontsize="15")
            plt.xlabel('Cumulative percentage of nodes', fontsize="15")
            plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="11")
            plt.grid(True)

            plt.tight_layout()

            virtual_file = BytesIO()
            plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
            virtual_file.seek(0)

            response = send_file(virtual_file, mimetype='image/png')
            response.headers['Content-Disposition'] = 'inline'
            return response

        elif(dataset == 'lorenzbychannelcountsbyentities' or dataset == 'lorenzbyliquiditybyentities'):
            plt.figure(figsize=(10, 6), linewidth=3)
            for i, year in enumerate(range(2018, 2024)):
                currentFocusedDate = str(year) + dayOfyear
                query = ''
                if(dataset == 'lorenzbychannelcountsbyentities'):
                    query = f'''
                        WITH ChannelCountData AS (
                            SELECT
                                ChannelCount,
                                NTILE(100) OVER (ORDER BY ChannelCount ASC) AS Percentile,
                                SUM(ChannelCount) OVER () AS TotalChannelCount
                            FROM 
                                _CACHED_TotalChannelCountNodesByTime
                            LEFT JOIN Lightning_NodeAliases
                                ON _CACHED_TotalChannelCountNodesByTime.Name = Lightning_NodeAliases.NodeID
                            LEFT JOIN Lightning_Entities
                                ON Lightning_NodeAliases.Alias = Lightning_Entities.Alias
                            WHERE
                                Date = ?
                            GROUP BY Lightning_Entities.Name
                        ),
                        PercentileAggregates AS (
                            SELECT
                                Percentile,
                                SUM(ChannelCount) AS SumChannelCount,
                                SUM(SUM(ChannelCount)) OVER (ORDER BY Percentile) AS CumulativeChannelCount,
                                MAX(TotalChannelCount) OVER () AS TotalChannelCount
                            FROM ChannelCountData
                            GROUP BY Percentile
                        ),
                        GetTable AS (
                            SELECT
                                Percentile,
                                CumulativeChannelCount,
                                ROUND((CumulativeChannelCount * 100.0 / TotalChannelCount), 1) AS CumulativePercentageOfChannelCount
                            FROM PercentileAggregates
                            ORDER BY Percentile
                        )

                        SELECT
                            Percentile, CumulativePercentageOfChannelCount
                        FROM
                            GetTable
                    '''
                elif(dataset == 'lorenzbyliquiditybyentities'):
                    query = f'''
                        WITH LiquidityData AS (
                            SELECT
                                Liquidity,
                                NTILE(100) OVER (ORDER BY Liquidity ASC) AS Percentile,
                                SUM(Liquidity) OVER () AS TotalLiquidity
                            FROM 
                                _CACHED_TotalLiquidityNodesByTime
                            LEFT JOIN Lightning_NodeAliases
                                ON _CACHED_TotalLiquidityNodesByTime.NodeID = Lightning_NodeAliases.NodeID
                            LEFT JOIN Lightning_Entities
                                ON Lightning_NodeAliases.Alias = Lightning_Entities.Alias
                            WHERE
                                Date = ?
                            GROUP BY Lightning_Entities.Name
                        ),
                        PercentileAggregates AS (
                            SELECT
                                Percentile,
                                SUM(Liquidity) AS SumLiquidity,
                                SUM(SUM(Liquidity)) OVER (ORDER BY Percentile) AS CumulativeLiquidity,
                                MAX(TotalLiquidity) OVER () AS TotalLiquidity
                            FROM LiquidityData
                            GROUP BY Percentile
                        ),
                        GetTable AS (
                            SELECT
                                Percentile,
                                CumulativeLiquidity,
                                ROUND((CumulativeLiquidity * 100.0 / TotalLiquidity), 1) AS CumulativePercentageOfLiquidity
                            FROM PercentileAggregates
                            ORDER BY Percentile
                        )

                        SELECT
                            Percentile, CumulativePercentageOfLiquidity
                        FROM
                            GetTable
                    '''

                sqlFetchData = conn.execute(query, [currentFocusedDate])
                data = sqlFetchData.fetchall()

                percentiles = [line[0] for line in data]
                cumulativePercentages = [line[1] for line in data]

                def calculate_gini(percentiles, cumulativePercentages):
                    percentiles = [0] + percentiles + [100]
                    cumulativePercentages = [0] + cumulativePercentages + [100]
                    
                    gini = 1 - sum((percentiles[i] - percentiles[i-1]) * (cumulativePercentages[i] + cumulativePercentages[i-1]) for i in range(1, len(percentiles))) / 10000
                    
                    return gini
                
                currentDateGini = calculate_gini(percentiles, cumulativePercentages)
                currentDateGini = round(currentDateGini, 3)

                plt.plot(percentiles, cumulativePercentages, label=f"T{i+1}: {currentFocusedDate} (Gini: {currentDateGini})")

            ax = plt.gca()
            ax.set_xlim(xmin=0, xmax=100)
            ax.set_ylim(ymin=0, ymax=100)
            ax.xaxis.tick_bottom()
            ax.yaxis.tick_right()
            ax.set_xticklabels([f'{int(tick)}%' for tick in plt.gca().get_xticks()])
            ax.set_yticklabels([f'{int(tick)}%' for tick in plt.gca().get_yticks()])
            ax.yaxis.set_label_position("right")

            plt.plot([0, 100], [0, 100], 'k--')
            plt.text(50, 55, 'Perfect Equality Line', rotation=30, ha='center', va='center')

            if(dataset == 'lorenzbychannelcountsbyentities'):
                plt.title('Lorenz curves of degree centrality (BLN Entities)', fontsize="15")
                plt.ylabel('Cumulative percentage of channels count', fontsize="15")
            elif(dataset == 'lorenzbyliquiditybyentities'):
                plt.title('Lorenz curves of weighted degree centrality (BLN Entities)', fontsize="15")
                plt.ylabel('Cumulative percentage of channels capacity', fontsize="15")
            plt.xlabel('Cumulative percentage of entities', fontsize="15")
            plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="15")
            plt.grid(True)

            plt.tight_layout()

            virtual_file = BytesIO()
            plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
            virtual_file.seek(0)

            response = send_file(virtual_file, mimetype='image/png')
            response.headers['Content-Disposition'] = 'inline'
            return response

    return Response('Chart not found', mimetype='text/plain', status=404)

# Add any additional routes or helper functions here if needed