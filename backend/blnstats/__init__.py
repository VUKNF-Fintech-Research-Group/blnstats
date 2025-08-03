from flask import Flask
import os
import gc
from datetime import datetime

from .database.utils import create_database_if_not_exists, create_tables_if_not_exists
from .database.raw_data_selector import RawDataSelector
from .database.node_metrics_selector import NodeMetricsSelector
from .database.entity_metrics_selector import EntityMetricsSelector

from .data_import.ln_research import LNResearchData

from .data_transform.entity_clusters import EntityClusters

from .calculations.coefficients import Coefficients
from .calculations.general_stats import GeneralStats

from .charts.chart_generator import BaseChartGenerator, LorenzCurveChartGenerator



import logging



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)






def create_app():
    # Create Database and Tables
    create_database_if_not_exists('lnstats')
    create_tables_if_not_exists()

    app = Flask(__name__)
    
    # Initialize extensions
    app.secret_key = b'903aef33213b836002bf60448f3713e45ab70828d1390523f527590037402188'
    app.config['SESSION_COOKIE_HTTPONLY'] = False

    from .api.auth.user import login_manager
    login_manager.init_app(app)

    
    # Register blueprints
    from .api.auth.routes import auth_bp


    app.register_blueprint(auth_bp, url_prefix='')
    
    return app






def generateCoefficientCharts(
    subjectsOfAnalysis=["Nodes", "Entities"],
    metricTypes=["weighted degree", "degree"],
    coefficientTypes=["Gini", "HHI", "Theil", "Normalized Theil", "Shannon Entropy", "Normalized Shannon Entropy", "Nakamoto", 
                    "Top 10 Percent Control Percentage", "Top 10 Percent Control Sum"]
):
    dateMask = '20XX-XX-01'
    
    # Chart variations
    # xTicksToGenerate = ["-03-01", "-06-01", "-09-01", "-12-01"]
    xTicksToGenerate = ["-03-01"]
    xTicksToExclude = ["-02-01", "-07-01", "-08-01"]
    figSizes = [(6, 10), (10, 6), (6, 6)]


    # Get first block heights of months
    firstBlocksOfMoths = RawDataSelector().get_first_blocks_of_days_by_date_mask(
        startSince='2018-02-01', endUntil=datetime.now().strftime('%Y-%m-%d'), dateMask=dateMask
    )

    for subjectOfAnalysis in subjectsOfAnalysis:
        for metricType in metricTypes:


            # Get Metrics Data Selector
            metricsDataSelector = None
            if(subjectOfAnalysis == "Nodes"):
                metricsDataSelector = NodeMetricsSelector()
            elif(subjectOfAnalysis == "Entities"):
                metricsDataSelector = EntityMetricsSelector()


            # Get Metrics Data
            verticesAspectData = None
            if(metricType == "weighted degree"):
                verticesAspectData = metricsDataSelector.get_capacity_metrics(firstBlocksOfMoths)
            elif(metricType == "degree"):
                verticesAspectData = metricsDataSelector.get_channel_count_metrics(firstBlocksOfMoths)


            # Save Metrics Data to File
            filePath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/{dateMask}.json'
            verticesAspectData.save_to_file(filePath)
            print(f"[*] Saved: {filePath}")


            for coefficientType in coefficientTypes:

                # Calculate Coefficient
                coefficientsData = Coefficients().calculate_on_vertices_data(verticesAspectData, coefficientType.replace(" ", ""))
                filePath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/{coefficientType.replace(" ", "_")}/{dateMask}.json'
                coefficientsData.save_to_file(filePath)
                print(f"[*] Saved: {filePath}")


                # Chart Generation
                for xTicksShowEndsWith in xTicksToGenerate:
                    for figsize in figSizes:
                        x_data = [item.date for item in coefficientsData.data.values()]
                        y_data = [item.value for item in coefficientsData.data.values()]

                        # Convert x_data to date objects
                        x_data = [datetime.strptime(x, '%Y-%m-%d') for x in x_data]


                        # Create folder path
                        folderPath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/{coefficientType.replace(" ", "_")}'
                        folderPath += f'/{"20XX"+xTicksShowEndsWith}'

                        # Initialize Chart Generator
                        chart_generator = BaseChartGenerator(x_data=x_data, y_data_list=[y_data], labels=[coefficientType])
                        chart_generator.customize_axes(
                            x_label='Time',
                            y_label=coefficientType,
                            title=f'{coefficientType} coefficient of {metricType}\ncentrality (BLN {subjectOfAnalysis})'
                        )
                        chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith, exclude_ends_with=xTicksToExclude)



                        # 1.) Generate Full Chart
                        chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
                        filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
                        chart_generator.save_chart(filePath)
                        print(f"[*] Saved: {filePath}")

                        # # 2.) Generate No Footer Chart
                        # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
                        # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
                        # chart_generator.save_chart(filePath)
                        # print(f"[*] Saved: {filePath}")

                        # 3.) Generate No Header/Footer Chart
                        filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
                        chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
                        chart_generator.save_chart(filePath)
                        print(f"[*] Saved: {filePath}")

                        # Clean Up Memory
                        gc.collect()







def generateOverlappingCoefficientCharts():
    dateMask = '20XX-XX-01'
    
    # Chart variations
    # xTicksToGenerate = ["-03-01", "-06-01", "-09-01", "-12-01"]
    xTicksToGenerate = ["-03-01"]
    xTicksToExclude = ["-02-01", "-07-01", "-08-01"]
    figSizes = [(6, 10), (10, 6), (6, 6)]

    # Analysis variations
    metricTypes = ["weighted degree", "degree"]
    coefficientTypes = ["Gini", "HHI", "Theil", "Normalized Theil", "Shannon Entropy", "Normalized Shannon Entropy", "Nakamoto", 
                        "Top 10 Percent Control Percentage", "Top 10 Percent Control Sum"]





    # Get first block heights of months
    firstBlocksOfMoths = RawDataSelector().get_first_blocks_of_days_by_date_mask(
        startSince='2018-02-01', endUntil=datetime.now().strftime('%Y-%m-%d'), dateMask=dateMask
    )

    for metricType in metricTypes:


        # Get Metrics Data
        verticesAspectDataNodes = None
        verticesAspectDataEntities = None
        if(metricType == "weighted degree"):
            verticesAspectDataNodes = NodeMetricsSelector().get_capacity_metrics(firstBlocksOfMoths)
            verticesAspectDataEntities = EntityMetricsSelector().get_capacity_metrics(firstBlocksOfMoths)
        elif(metricType == "degree"):
            verticesAspectDataNodes = NodeMetricsSelector().get_channel_count_metrics(firstBlocksOfMoths)
            verticesAspectDataEntities = EntityMetricsSelector().get_channel_count_metrics(firstBlocksOfMoths)


        for coefficientType in coefficientTypes:

            # Calculate Coefficient
            coefficientsDataEntities = Coefficients().calculate_on_vertices_data(verticesAspectDataEntities, coefficientType.replace(" ", ""))
            coefficientsDataNodes = Coefficients().calculate_on_vertices_data(verticesAspectDataNodes, coefficientType.replace(" ", ""))


            # Chart Generation
            for xTicksShowEndsWith in xTicksToGenerate:
                for figsize in figSizes:
                    x_data = [item.date for item in coefficientsDataEntities.data.values()]
                    y_data_entities = [item.value for item in coefficientsDataEntities.data.values()]
                    y_data_nodes = [item.value for item in coefficientsDataNodes.data.values()]

                    # Convert x_data to date objects
                    x_data = [datetime.strptime(x, '%Y-%m-%d') for x in x_data]


                    # Create folder path
                    folderPath = f'/DATA/GENERATED/EntitiesNodes/{metricType.replace(" ", "_")}/{coefficientType.replace(" ", "_")}'
                    folderPath += f'/{"20XX"+xTicksShowEndsWith}'

                    # Initialize Chart Generator
                    chart_generator = BaseChartGenerator(
                        x_data=x_data,
                        y_data_list=[y_data_entities, y_data_nodes],
                        labels=[coefficientType+" (Entities)", coefficientType+" (Nodes)"]
                    )
                    chart_generator.customize_axes(
                        x_label='Time',
                        y_label=coefficientType,
                        title=f'{coefficientType} coefficient of {metricType}\ncentrality (BLN Entities and Nodes)'
                    )
                    chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith, exclude_ends_with=xTicksToExclude)



                    # 1.) Generate Full Chart
                    chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # # 2.) Generate No Footer Chart
                    # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
                    # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
                    # chart_generator.save_chart(filePath)
                    # print(f"[*] Saved: {filePath}")

                    # 3.) Generate No Header/Footer Chart
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
                    chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # Clean Up Memory
                    gc.collect()











def generateCoefficientsOnSingleChart():
    dateMask = '20XX-XX-01'

    # Chart variations
    # xTicksToGenerate = ["-03-01", "-06-01", "-09-01", "-12-01"]
    xTicksToGenerate = ["-03-01"]
    xTicksToExclude = ["-02-01", "-07-01", "-08-01"]
    figSizes = [(6, 10), (10, 6), (6, 6)]

    # Analysis variations
    subjectsOfAnalysis = ["Nodes", "Entities"]
    metricTypes = ["weighted degree", "degree"]




    # Get first block heights of months
    firstBlocksOfMoths = RawDataSelector().get_first_blocks_of_days_by_date_mask(
        startSince='2018-02-01', endUntil=datetime.now().strftime('%Y-%m-%d'), dateMask=dateMask
    )

    for subjectOfAnalysis in subjectsOfAnalysis:
        for metricType in metricTypes:

            # Get Metrics Data Selector
            metricsDataSelector = None
            if(subjectOfAnalysis == "Nodes"):
                metricsDataSelector = NodeMetricsSelector()
            elif(subjectOfAnalysis == "Entities"):
                metricsDataSelector = EntityMetricsSelector()


            # Get Metrics Data
            verticesAspectData = None
            if(metricType == "weighted degree"):
                verticesAspectData = metricsDataSelector.get_capacity_metrics(firstBlocksOfMoths)
            elif(metricType == "degree"):
                verticesAspectData = metricsDataSelector.get_channel_count_metrics(firstBlocksOfMoths)


            # Calculate Coefficients
            giniCoefData = Coefficients().calculate_on_vertices_data(verticesAspectData, "Gini")
            hhiCoefData = Coefficients().calculate_on_vertices_data(verticesAspectData, "HHI")
            normalizedTheilCoefData = Coefficients().calculate_on_vertices_data(verticesAspectData, "NormalizedTheil")
            normalizedShannonEntropyCoefData = Coefficients().calculate_on_vertices_data(verticesAspectData, "NormalizedShannonEntropy")


            # Chart Generation
            for xTicksShowEndsWith in xTicksToGenerate:
                for figsize in figSizes:
                    x_data = [item.date for item in giniCoefData.data.values()]
                    
                    y_data_gini = [item.value for item in giniCoefData.data.values()]
                    y_data_hhi = [item.value / 10000 for item in hhiCoefData.data.values()]
                    y_data_normalizedTheil = [item.value for item in normalizedTheilCoefData.data.values()]
                    y_data_normalizedShannonEntropy = [item.value for item in normalizedShannonEntropyCoefData.data.values()]


                    # Convert x_data to date objects
                    x_data = [datetime.strptime(date, '%Y-%m-%d').date() for date in x_data]                

                    # Add y_data to single list
                    y_data_list = [y_data_gini, y_data_hhi, y_data_normalizedTheil, y_data_normalizedShannonEntropy]


                    # Create folder path
                    folderPath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/Gini_HHI_NormTheil_NormShannonEntropy'
                    folderPath += f'/{"20XX"+xTicksShowEndsWith}'

                    # Initialize Chart Generator
                    chart_generator = BaseChartGenerator(
                        x_data=x_data, 
                        y_data_list=y_data_list, 
                        labels=["Gini", "HHI", "Normalized Theil", "Normalized Shannon Entropy"]
                    )
                    chart_generator.customize_axes(
                        x_label='Time',
                        y_label='Coefficient Value',
                        title=f'Gini, HHI, Normalized Theil, Normalized Shannon Entropy\nof {metricType} centrality (BLN {subjectOfAnalysis})',
                        y_lim=(0, 1.2),
                    )
                    chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith, exclude_ends_with=xTicksToExclude)



                    # 1.) Generate Full Chart
                    chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # # 2.) Generate No Footer Chart
                    # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
                    # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
                    # chart_generator.save_chart(filePath)
                    # print(f"[*] Saved: {filePath}")

                    # 3.) Generate No Header/Footer Chart
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
                    chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # Clean Up Memory
                    gc.collect()








def calculate_gini_from_lorenz(percentiles, cumulative_percentages):
    """
    Calculates the Gini coefficient from Lorenz curve data.

    Parameters:
    percentiles (list or numpy array): Cumulative percentages of the population (e.g., [0, 10, 20, ..., 100])
    cumulative_percentages (list or numpy array): Corresponding cumulative percentages of wealth/income/etc.

    Returns:
    float: The Gini coefficient.
    """

    # Ensure the lists start at 0% and end at 100%
    if percentiles[0] != 0 or cumulative_percentages[0] != 0:
        percentiles = [0] + percentiles
        cumulative_percentages = [0] + cumulative_percentages
    if percentiles[-1] != 100 or cumulative_percentages[-1] != 100:
        percentiles.append(100)
        cumulative_percentages.append(100)

    # Convert percentages to proportions (0 to 1)
    X = [p / 100.0 for p in percentiles]
    Y = [cp / 100.0 for cp in cumulative_percentages]

    # Calculate the area under the Lorenz curve using the trapezoidal rule
    area_under_lorenz = 0.0
    for i in range(1, len(X)):
        width = X[i] - X[i - 1]
        height = (Y[i] + Y[i - 1]) / 2.0
        area_under_lorenz += width * height

    # The area between the line of perfect equality and the Lorenz curve
    area_between = 0.5 - area_under_lorenz

    # Gini coefficient is twice the area between the line of equality and the Lorenz curve
    gini_coefficient = 2 * area_between

    return gini_coefficient








def generateLorenzCharts():
    # dateMasks = ['20XX-03-01', '20XX-06-01', '20XX-09-01', '20XX-12-01']
    dateMasks = ['20XX-03-01']

    # Chart variations
    figSizes = [(6, 10), (10, 6), (6, 6)]

    # Analysis variations
    subjectsOfAnalysis = ["Nodes", "Entities"]
    # subjectsOfAnalysis = ["Entities"]
    metricTypes = ["weighted degree", "degree"]



    for dateMask in dateMasks:

        # Get first block heights of selected date mask
        blockHeightsData = RawDataSelector().get_first_blocks_of_days_by_date_mask(
            startSince='2018-01-01', endUntil=datetime.now().strftime('%Y-%m-%d'), dateMask=dateMask
        )


        for subjectOfAnalysis in subjectsOfAnalysis:
            for metricType in metricTypes:

                # Get Metrics Data Selector
                metricsDataSelector = None
                if(subjectOfAnalysis == "Nodes"):
                    metricsDataSelector = NodeMetricsSelector()
                elif(subjectOfAnalysis == "Entities"):
                    metricsDataSelector = EntityMetricsSelector()


                # Get Metrics Data
                verticesAspectData = None
                if(metricType == "weighted degree"):
                    verticesAspectData = metricsDataSelector.get_capacity_metrics(blockHeightsData)
                elif(metricType == "degree"):
                    verticesAspectData = metricsDataSelector.get_channel_count_metrics(blockHeightsData)



                # Save Metrics Data to File
                filePath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/{dateMask}.json'
                verticesAspectData.save_to_file(filePath)
                print(f"[*] Saved: {filePath}")




                # Calculate Gini Coefficient
                coefficientType = "Gini"
                coefficientsData = Coefficients().calculate_on_vertices_data(verticesAspectData, coefficientType.replace(" ", ""))
                filePath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/{coefficientType.replace(" ", "_")}/{dateMask}.json'
                coefficientsData.save_to_file(filePath)
                print(f"[*] Saved: {filePath}")



                # Prepare datasets for Lorenz curves
                datasets = []
                timestampID = 0
                for blockHeight in verticesAspectData.data:
                    timestampID += 1
                    date = verticesAspectData.data[blockHeight].date

                    print(blockHeight)
                    nodesmetricsData = verticesAspectData.data[blockHeight].vertices

                    # Sort the data based on the 'value' field
                    sorted_data = sorted(nodesmetricsData, key=lambda x: x.value)

                    # Calculate cumulative sum of the 'value' field
                    cumulative_sum = [sum(item.value for item in sorted_data[:i+1]) for i in range(len(sorted_data))]

                    # Normalize cumulative sum to get cumulative percentage
                    total = cumulative_sum[-1]
                    cumulative_percentages = [x / total * 100 for x in cumulative_sum]

                    # Calculate percentiles
                    percentiles = [(i + 1) / len(sorted_data) * 100 for i in range(len(sorted_data))]

                    giniCoefficient = round(coefficientsData.data[blockHeight].value, 3)
                    datasets.append({
                        'percentiles': percentiles,
                        'cumulative_percentages': cumulative_percentages,
                        'label': f"T{timestampID}: {date} (Gini: {giniCoefficient:.3f})"
                    })

                    # Double check with gini calculator from Lorenz curve
                    giniCoefficientFromLorenzCurve = calculate_gini_from_lorenz(percentiles, cumulative_percentages)
                    print(f"T{timestampID}: {date} (GiniFromLorenzCurve: {giniCoefficientFromLorenzCurve})")




                # Plot Lorenz Curve
                for figsize in figSizes:
                    title, y_label = '', ''
                    if(metricType == 'degree'):
                        title = 'Lorenz curves of degree centrality'
                        y_label = 'Cumulative percentage of channels count'
                    elif(metricType == 'weighted degree'):
                        title = 'Lorenz curves of weighted degree\ncentrality'
                        y_label = 'Cumulative percentage of channels capacity'



                    # Create folder path
                    folderPath = f'/DATA/GENERATED/{subjectOfAnalysis}/{metricType.replace(" ", "_")}/Lorenz_Curves'
                    folderPath += f'/{dateMask}'


                    # Initialize Chart Generator
                    chart_generator = LorenzCurveChartGenerator(
                        datasets=datasets,
                    )
                    chart_generator.customize_axes(
                        x_label=f'Cumulative percentage of {subjectOfAnalysis.lower()}',
                        y_label=y_label,
                        title=title + f" (BLN {subjectOfAnalysis})",
                        # y_lim=(0, 1.2),
                    )

                    # 1.) Generate Full Chart
                    chart_generator.generate_lorenz_curves(figsize=figsize, print_header=True, print_footer=True)
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # # 2.) Generate No Footer Chart
                    # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
                    # chart_generator.generate_lorenz_curves(figsize=figsize, print_header=True, print_footer=False)
                    # chart_generator.save_chart(filePath)
                    # print(f"[*] Saved: {filePath}")

                    # 3.) Generate No Header/Footer Chart
                    filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
                    chart_generator.generate_lorenz_curves(figsize=figsize, print_header=False, print_footer=False)
                    chart_generator.save_chart(filePath)
                    print(f"[*] Saved: {filePath}")

                    # Clean Up Memory
                    gc.collect()





def generateExampleLorenzCharts():
    for figsize in [(6, 6), (10, 6), (6, 10)]:

        # Initialize Chart Generator
        chart_generator = LorenzCurveChartGenerator()

        # 1.) Generate Full Chart
        chart_generator.generate_example_lorenz_curve(figsize=figsize, print_header=True, print_footer=True)
        filePath = f'/DATA/GENERATED/Examples/Lorenz_Curves/{figsize[0]}x{figsize[1]}_Full.svg'
        chart_generator.save_chart(filePath)
        print(f"[*] Saved: {filePath}")


        # # 2.) Generate No Footer Chart
        # chart_generator.generate_example_lorenz_curve(figsize=figsize, print_header=False, print_footer=True)
        # filePath = f'/DATA/GENERATED/Examples/Lorenz_Curves/{figsize[0]}x{figsize[1]}_NoFooter.svg'
        # chart_generator.save_chart(filePath)
        # print(f"[*] Saved: {filePath}")


        # 3.) Generate No Header/Footer Chart
        chart_generator.generate_example_lorenz_curve(figsize=figsize, print_header=False, print_footer=False)
        filePath = f'/DATA/GENERATED/Examples/Lorenz_Curves/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
        chart_generator.save_chart(filePath)
        print(f"[*] Saved: {filePath}")








def generateGeneralStatisticsCharts():
    dateMask = '20XX-XX-01'

    # Chart variations
    # xTicksToGenerate = ["-03-01", "-06-01", "-09-01", "-12-01"]
    xTicksToGenerate = ["-03-01"]
    figSizes = [(6, 10), (10, 6), (6, 6)]
    

    # Get first block heights of months
    firstBlocksOfMoths = RawDataSelector().get_first_blocks_of_days_by_date_mask(
        startSince='2018-02-01', endUntil=datetime.now().strftime('%Y-%m-%d'), dateMask=dateMask
    )


    # Get Metrics Data (Weighted Degree)
    vertices_capacity_data =        NodeMetricsSelector().get_capacity_metrics(firstBlocksOfMoths)
    vertices_channel_count_data =   NodeMetricsSelector().get_channel_count_metrics(firstBlocksOfMoths)

    # Calculate General Stats
    general_stats_data = GeneralStats().calculate(vertices_capacity_data, vertices_channel_count_data)
    general_stats_data.save_to_file(f'/DATA/GENERATED/General_Stats/{dateMask}.json')


    # Prepare data for charts
    date_data = [item.date for item in general_stats_data.data.values()]
    node_count_data = [item.node_count for item in general_stats_data.data.values()]
    node_capacity_data = [item.network_capacity for item in general_stats_data.data.values()]
    channel_count_data = [item.channel_count for item in general_stats_data.data.values()]


    # Convert date_data to date objects
    date_data = [datetime.strptime(date, '%Y-%m-%d').date() for date in date_data] 


    # Chart Generation
    for xTicksShowEndsWith in xTicksToGenerate:
        for figsize in figSizes:



            ######################### NODE COUNT CHART #########################
            # Create folder path
            folderPath = f'/DATA/GENERATED/General_Stats/Node_Count'
            folderPath += f'/{"20XX"+xTicksShowEndsWith}'

            # Initialize Chart Generator
            chart_generator = BaseChartGenerator(x_data=date_data, y_data_list=[node_count_data], labels=["Total Number of Nodes"])
            chart_generator.customize_axes(
                x_label='Time',
                y_label="Total Number of Nodes",
                title=f'Total number of BLN nodes in the network'
            )
            chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith)

            # 1.) Generate Full Chart
            chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")

            # # 2.) Generate No Footer Chart
            # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
            # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
            # chart_generator.save_chart(filePath)
            # print(f"[*] Saved: {filePath}")

            # 3.) Generate No Header/Footer Chart
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
            chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")
            ####################################################################




            ###################### NETWORK CAPACITY CHART ######################
            # Create folder path
            folderPath = f'/DATA/GENERATED/General_Stats/Network_Capacity'
            folderPath += f'/{"20XX"+xTicksShowEndsWith}'

            # Initialize Chart Generator
            chart_generator = BaseChartGenerator(x_data=date_data, y_data_list=[node_capacity_data], labels=["Total Network Capacity (BTC)"])
            chart_generator.customize_axes(
                x_label='Time',
                y_label="Total Network Capacity (BTC)",
                title=f'Total network capacity in the BLN network'
            )
            chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith)

            # 1.) Generate Full Chart
            chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")

            # # 2.) Generate No Footer Chart
            # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
            # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
            # chart_generator.save_chart(filePath)
            # print(f"[*] Saved: {filePath}")

            # 3.) Generate No Header/Footer Chart
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
            chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")
            ####################################################################




            ###################### CHANNEL COUNT CHART ######################
            # Create folder path
            folderPath = f'/DATA/GENERATED/General_Stats/Channel_Count'
            folderPath += f'/{"20XX"+xTicksShowEndsWith}'

            # Initialize Chart Generator
            chart_generator = BaseChartGenerator(x_data=date_data, y_data_list=[channel_count_data], labels=["Total Channel Count"])
            chart_generator.customize_axes(
                x_label='Time',
                y_label="Total Channel Count",
                title=f'Total channel count in the BLN network'
            )
            chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith)

            # 1.) Generate Full Chart
            chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=True)
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_Full.svg'
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")

            # # 2.) Generate No Footer Chart
            # filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoFooter.svg'
            # chart_generator.generate_line_chart(figsize=figsize, print_header=True, print_footer=False)
            # chart_generator.save_chart(filePath)
            # print(f"[*] Saved: {filePath}")

            # 3.) Generate No Header/Footer Chart
            filePath = folderPath + f'/{figsize[0]}x{figsize[1]}_NoHeaderFooter.svg'
            chart_generator.generate_line_chart(figsize=figsize, print_header=False, print_footer=False)
            chart_generator.save_chart(filePath)
            print(f"[*] Saved: {filePath}")
            ####################################################################



def compare_data_sources():
    from blnstats.data_import.compare_sources import CompareSources
    xTicksShowEndsWith = "-03-01"
    xTicksToExclude = ["-01-01", "-02-01"]
    CompareSources(xTicksShowEndsWith, xTicksToExclude)








def test_entity_functionality():
    entityObj = EntityClusters()
    entityObj.import_node_aliases_to_main_table(
        from_table_name='_LNResearch_NodeAnnouncements',
        from_alias_column='alias',
        from_node_id_column='node_id',
        from_timestamp_column='timestamp'
    )
    entityObj.import_new_entities_to_main_table()
    entityObj.fix_entity_hex_names_if_possible()
    entityObj.test_functionality()






def generateCSV_EntityMetrics(dateMasks):
    for dateMask in dateMasks:

        # Get Block Heights for the date mask
        blockHeightsStructure = RawDataSelector().get_first_blocks_of_days_by_date_mask(
            dateMask=dateMask, 
            startSince='2018-01-01', 
            endUntil=datetime.now().strftime('%Y-%m-%d')
        )

        # Calculate Entity capacity metrics and save to CSV
        EntityMetricsSelector().get_capacity_metrics(blockHeightsStructure).save_to_csv(
            filePath=f'/DATA/GENERATED/Entities/weighted_degree/DATA_CSV/EntityCapacityDate_{dateMask}.csv',
            divideValueBy=100000000.0
        )

        # Calculate Entity channel count metrics and save to CSV
        EntityMetricsSelector().get_channel_count_metrics(blockHeightsStructure).save_to_csv(
            filePath=f'/DATA/GENERATED/Entities/degree/DATA_CSV/EntityChannelCountDate_{dateMask}.csv',
        )





def synchronizeBlockchain():
    '''
    This function synchronizes the blockchain with the database.
    It is used to ensure that the database is up to date with the latest blocks and transactions.
    '''
    
    # IMPORT BLOCKS:
    # Sync missing blocks from the latest in the database to the latest in the blockchain
    from .data_import.blockchain_blocks import BlockchainBlocks
    BlockchainBlocks(
        electrum_host=os.getenv('BLNSTATS_ELECTRUM_HOST'),
        electrum_port=int(os.getenv('BLNSTATS_ELECTRUM_PORT', 50001))
    ).sync_blocks()


    # IMPORT TRANSACTIONS:
    # Import transactions from the latest in the database to the latest in the blockchain
    from .data_import.blockchain_transactions import BlockchainTransactions
    BlockchainTransactions(
        electrum_host=os.getenv('BLNSTATS_ELECTRUM_HOST'),
        electrum_port=int(os.getenv('BLNSTATS_ELECTRUM_PORT', 50001))
    ).run(500)


    # IMPORT BLOCKS:
    # Sync missing blocks from the latest in the database to the latest in the blockchain
    from .data_import.blockchain_blocks import BlockchainBlocks
    BlockchainBlocks(
        electrum_host=os.getenv('BLNSTATS_ELECTRUM_HOST'),
        electrum_port=int(os.getenv('BLNSTATS_ELECTRUM_PORT', 50001))
    ).sync_blocks()






def importLNDDBReader(file_path):

    # Import LND DBReader data
    from .data_import.lnd_dbreader import LNDDBReader
    LNDDBReader(file_path)

    # Import node aliases to main table
    entityObj = EntityClusters()
    entityObj.import_node_aliases_to_main_table(
        from_table_name='_LND_DBReader_NodeAnnouncements',
        from_alias_column='Alias',
        from_node_id_column='NodeID',
        from_timestamp_column='LastSeen'
    )
    entityObj.import_new_entities_to_main_table()
    entityObj.fix_entity_hex_names_if_possible()
    entityObj.test_functionality()






def transformNodeMetrics():
    from .data_transform.node_metrics import NodeMetrics
    nodeMetrics = NodeMetrics()

    # Transformuoti vieno bloko momentą
    nodeMetrics.transformForBlockHeight(505000)
    
    # Transformuoti visų mėnesių pirmą bloką
    nodeMetrics.transformForFirstBlocksOfMonths()
