
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors
# import numpy as np

# def generateRainbowChart():
#     print("Starting the rainbow chart generation...")

#     # Get first block heights of months
#     print("Fetching block heights...")
#     blockHeightsStructure = RawDataSelector().get_first_blocks_of_days_by_date_mask(
#         startSince='2018-02-01', endUntil='2023-09-24', dateMask='20XX-XX-01'
#     )

#     print("Fetching entity capacity metrics...")
#     entityCapacityMetricsData = EntityMetricsSelector().get_capacity_metrics(blockHeightsStructure)

#     # Prepare data for plotting
#     data = {}
#     for blockHeight in entityCapacityMetricsData.data.keys():
#         date = entityCapacityMetricsData.data[blockHeight].date
#         print(f"Processing data for date: {date}")
#         entitiesArray = entityCapacityMetricsData.data[blockHeight].vertices

#         # Sort entities by value and get top N
#         sorted_entities = sorted(entitiesArray, key=lambda x: x.value, reverse=True)
#         top_entities = sorted_entities[:50]
#         others_value = sum(entity.value for entity in sorted_entities[50:])

#         # Prepare data for the current date
#         total_value = sum(entity.value for entity in sorted_entities)
#         data[date] = {entity.name: entity.value / total_value for entity in top_entities}
#         data[date]['Others'] = others_value / total_value

#     print("Converting data to DataFrame...")
#     df = pd.DataFrame(data).T.fillna(0)

#     # **Reordering the DataFrame Columns**
#     # Calculate the total value for each entity over time
#     entity_totals = df.sum(axis=0)
#     # Sort entities so that larger ones are at the bottom
#     sorted_entities = entity_totals.sort_values(ascending=False).index.tolist()
#     df = df[sorted_entities]

#     # **Generating Colors for Entities**
#     entities = df.columns.tolist()
#     num_entities = len(entities)

#     print("Generating colors for entities...")
#     # Generate a custom colormap with enough distinct colors
#     colors = plt.cm.get_cmap('tab20b')(np.linspace(0, 1, num_entities))
#     colors = [mcolors.rgb2hex(color) for color in colors]

#     # Set 'Others' to grey
#     if 'Others' in entities:
#         index = entities.index('Others')
#         colors[index] = 'grey'

#     print("Generating the plot...")
#     plt.figure(figsize=(14, 8))
#     df.plot.area(stacked=True, linewidth=0, legend=False, color=colors)

#     plt.title('Entity Capacity Distribution Over Time')
#     plt.xlabel('Date')
#     plt.ylabel('Capacity Distribution')
#     plt.tight_layout()

#     print("Saving the chart to file...")
#     plt.savefig('./GENERATED/rainbow.png', bbox_inches='tight', dpi=300)
#     plt.close()

#     print("Rainbow chart generation completed.")






import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def generateRainbowChart():
    print("Starting the rainbow chart generation...")

    # Get first block heights of months
    print("Fetching block heights...")
    blockHeightsStructure = RawDataSelector().get_first_blocks_of_days_by_date_mask(
        startSince='2018-02-01', endUntil='2023-09-24', dateMask='20XX-XX-01'
    )

    print("Fetching entity capacity metrics...")
    entityCapacityMetricsData = EntityMetricsSelector().get_capacity_metrics(blockHeightsStructure)

    # Prepare data for plotting
    data = {}
    color_map = {}
    color_palette = plt.cm.tab20.colors  # You can choose any colormap you prefer
    color_index = 0

    for blockHeight in sorted(entityCapacityMetricsData.data.keys()):
        date = entityCapacityMetricsData.data[blockHeight].date
        print(f"Processing data for date: {date}")
        entitiesArray = entityCapacityMetricsData.data[blockHeight].vertices

        # Sort entities by value at this timeframe
        sorted_entities = sorted(entitiesArray, key=lambda x: x.value, reverse=True)
        top_entities = sorted_entities[:20]
        others_value = sum(entity.value for entity in sorted_entities[20:])

        # Prepare data for the current date
        total_value = sum(entity.value for entity in sorted_entities)
        data[date] = {}
        for entity in top_entities:
            proportion = entity.value / total_value
            data[date][entity.name] = proportion

            # Assign color if not already assigned
            if entity.name not in color_map:
                color_map[entity.name] = color_palette[color_index % len(color_palette)]
                color_index += 1

        # Add 'Others' category
        others_proportion = others_value / total_value
        data[date]['Others'] = others_proportion

        # Assign color to 'Others' if not already assigned
        if 'Others' not in color_map:
            color_map['Others'] = 'grey'

    print("Converting data to DataFrame...")
    df = pd.DataFrame(data).T.fillna(0)

    # **Plotting the Data**
    print("Generating the plot...")
    fig, ax = plt.subplots(figsize=(14, 8))

    # Sort dates
    dates = sorted(df.index)
    indices = np.arange(len(dates))

    # Initialize bottom positions for stacking
    bottoms = np.zeros(len(dates))

    # Get list of all entities
    all_entities = []
    for date in dates:
        entities = df.loc[date][df.loc[date] > 0].index.tolist()
        for entity in entities:
            if entity not in all_entities:
                all_entities.append(entity)

    # Plot each entity
    for entity in all_entities:
        values = df[entity].values
        ax.bar(
            indices,
            values,
            bottom=bottoms,
            width=0.8,
            color=color_map[entity],
            edgecolor='none',
            label=entity if entity != 'Others' else ''
        )
        bottoms += values

    # Formatting the x-axis with dates
    ax.set_xticks(indices)
    ax.set_xticklabels(dates, rotation=45, ha='right')

    ax.set_title('Entity Capacity Distribution Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Capacity Distribution')

    # Remove legend
    ax.legend().remove()

    plt.tight_layout()

    print("Saving the chart to file...")
    plt.savefig('./GENERATED/rainbow.png', bbox_inches='tight', dpi=300)
    plt.close()

    print("Rainbow chart generation completed.")