import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from io import BytesIO
from datetime import datetime
from ..db.utils import get_db_connection



def generate_gini_chart(dataset):
    dayOfyear = '-06-01'
    plt.figure(figsize=(4, 6), linewidth=3)

    with get_db_connection() as conn:
        query = ''
        if dataset == 'ginichannelcountbynodes':
            query = '''
                SELECT
                    Date, ROUND(Gini, 3)
                FROM
                    _CACHED_GiniChannelCount
                WHERE
                    Date <= '2023-09-24'
            '''
        elif dataset == 'giniliquiditybynodes':
            query = '''
                SELECT
                    Date, ROUND(Gini, 3)
                FROM
                    _CACHED_GiniLiquidity
                WHERE
                    Date <= '2023-09-24'
            '''
        
        sqlFetchData = conn.execute(query)
        data = sqlFetchData.fetchall()

    dates = [datetime.strptime(line[0], '%Y-%m-%d') for line in data]
    gini = [line[1] for line in data]
    plt.plot(dates, gini, label="Gini Coefficient")

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

    return virtual_file






def generate_lorenz_example():
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

    return virtual_file






def generate_total_nodes_chart():
    plt.figure(figsize=(10, 6), linewidth=3)
    
    with get_db_connection() as conn:
        query = '''
            SELECT
                Date, Value
            FROM
                _CACHED_Chart_NodeCount
            WHERE
                Date <= '2023-09-24'
        '''
        sqlFetchData = conn.execute(query)
        data = sqlFetchData.fetchall()

    dates = [datetime.strptime(line[0], '%Y-%m-%d') for line in data]
    nodecount = [line[1] for line in data]
    plt.plot(dates, nodecount, label="Node Count")

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    xticks = [dates[0], dates[-1]] + [date for date in dates if date.strftime('%m-%d') == '03-01' and date.strftime('%Y-%m-%d') != '2018-03-01']
    ax.set_xticks(xticks)

    plt.gcf().autofmt_xdate()

    plt.title('BLN node count throughout time', fontsize="15")
    plt.xlabel('Time', fontsize="15")
    plt.ylabel('BLN Node Count', fontsize="15")
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="15")
    plt.grid(True)

    plt.tight_layout()

    virtual_file = BytesIO()
    plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
    virtual_file.seek(0)

    return virtual_file






def generate_lorenz_curve(dataset):
    dayOfyear = '-06-01'
    plt.figure(figsize=(6, 6), linewidth=3)

    with get_db_connection() as conn:
        for i, year in enumerate(range(2018, 2024)):
            currentFocusedDate = str(year) + dayOfyear
            query = ''
            if dataset == 'lorenzbychannelcountsbynodes':
                query = '''
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
            elif dataset == 'lorenzbyliquiditybynodes':
                query = '''
                    WITH LiquidityData AS (
                        SELECT
                            Liquidity,
                            NTILE(100) OVER (ORDER BY Liquidity ASC) AS Percentile,
                            SUM(Liquidity) OVER () AS TotalLiquidity
                        FROM _CACHED_TotalLiquidityNodesByTime
                        WHERE Date = ?
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

    if dataset == 'lorenzbychannelcountsbynodes':
        plt.title('Lorenz curves of degree centrality (BLN Nodes)', fontsize="15")
        plt.ylabel('Cumulative percentage of channels count', fontsize="15")
    elif dataset == 'lorenzbyliquiditybynodes':
        plt.title('Lorenz curves of weighted degree\ncentrality (BLN Nodes)', fontsize="15")
        plt.ylabel('Cumulative percentage of channels capacity', fontsize="15")
    plt.xlabel('Cumulative percentage of nodes', fontsize="15")
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="11")
    plt.grid(True)

    plt.tight_layout()

    virtual_file = BytesIO()
    plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
    virtual_file.seek(0)

    return virtual_file








def generate_lorenz_curve_by_entities(dataset):
    dayOfyear = '-06-01'
    plt.figure(figsize=(10, 6), linewidth=3)

    with get_db_connection() as conn:
        for i, year in enumerate(range(2018, 2024)):
            currentFocusedDate = str(year) + dayOfyear
            query = ''
            if dataset == 'lorenzbychannelcountsbyentities':
                query = '''
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
            elif dataset == 'lorenzbyliquiditybyentities':
                query = '''
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

    if dataset == 'lorenzbychannelcountsbyentities':
        plt.title('Lorenz curves of degree centrality (BLN Entities)', fontsize="15")
        plt.ylabel('Cumulative percentage of channels count', fontsize="15")
    elif dataset == 'lorenzbyliquiditybyentities':
        plt.title('Lorenz curves of weighted degree centrality (BLN Entities)', fontsize="15")
        plt.ylabel('Cumulative percentage of channels capacity', fontsize="15")
    plt.xlabel('Cumulative percentage of entities', fontsize="15")
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize="15")
    plt.grid(True)

    plt.tight_layout()

    virtual_file = BytesIO()
    plt.savefig(virtual_file, format='png', bbox_inches='tight', pad_inches=0.2, edgecolor='#555555', dpi=1000)
    virtual_file.seek(0)

    return virtual_file






def generate_chart(dataset, selected_time=None):
    if dataset in ['ginichannelcountbynodes', 'giniliquiditybynodes']:
        return generate_gini_chart(dataset)
    elif dataset == 'lorenzexample':
        return generate_lorenz_example()
    elif dataset == 'totalnodesbytime':
        return generate_total_nodes_chart()
    elif dataset in ['lorenzbychannelcountsbynodes', 'lorenzbyliquiditybynodes']:
        return generate_lorenz_curve(dataset)
    elif dataset in ['lorenzbychannelcountsbyentities', 'lorenzbyliquiditybyentities']:
        return generate_lorenz_curve_by_entities(dataset)
    else:
        raise ValueError(f"Unknown dataset: {dataset}")





# Helper functions

def timestamp_to_datetime_string(timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')

# Add any additional helper functions here if needed




