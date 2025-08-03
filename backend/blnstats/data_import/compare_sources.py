import logging
import json
from ..database.utils import get_db_connection
from ..charts.chart_generator import BaseChartGenerator
from datetime import datetime
import gc
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





class CompareSources:

    def __init__(self, xTicksToGenerate, xTicksToExclude):
        general_stats = self.compare_sources(
            source_db_table1="_LNResearch_ChannelAnnouncements",
            column_name1="ShortChannelID",
            source_db_table2="_LND_DBReader_ChannelAnnouncements",
            column_name2="ShortChannelID"
        )
        os.makedirs("/DATA/GENERATED/Compare_Sources/Channel_Announcements", exist_ok=True)
        with open("/DATA/GENERATED/Compare_Sources/Channel_Announcements/compare_sources.json", "w") as f:
            json.dump(general_stats, f, indent=4)

        stats_across_time = self.compare_sources_across_time()
        with open("/DATA/GENERATED/Compare_Sources/Channel_Announcements/compare_sources_across_time.json", "w") as f:
            json.dump(stats_across_time, f, indent=4)
        self.plot_data(stats_across_time, xTicksToGenerate, xTicksToExclude)



    def compare_sources(self, source_db_table1, column_name1, source_db_table2, column_name2):
        with get_db_connection() as db_conn:
            with db_conn.cursor() as db_cursor:

                # Get the number of rows in each table
                db_cursor.execute(f"SELECT COUNT(*) FROM {source_db_table1}")
                count1 = db_cursor.fetchone()[0]
                
                db_cursor.execute(f"SELECT COUNT(*) FROM {source_db_table2}")
                count2 = db_cursor.fetchone()[0]

                # Get the number of rows in the overlap of the two tables
                db_cursor.execute(f"SELECT COUNT(*) FROM {source_db_table1} INNER JOIN {source_db_table2} ON {source_db_table1}.{column_name1} = {source_db_table2}.{column_name2}")
                overlap_count = db_cursor.fetchone()[0]

                return {
                    source_db_table1: count1,
                    source_db_table2: count2,
                    "overlap": overlap_count,
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }



    def compare_sources_across_time(self):
        def get_monthly_counts(cursor, query):
            cursor.execute(query)
            return cursor.fetchall()

        data = {}
        with get_db_connection() as cnx:
            with cnx.cursor(dictionary=True) as cursor:

                # Query for _LNResearch_ChannelAnnouncements table.
                query_research = """
                    SELECT DATE_FORMAT(b.Date, '%Y-%m') AS month, COUNT(*) AS count
                    FROM _LNResearch_ChannelAnnouncements a
                    JOIN Blockchain_Blocks b ON a.BlockIndex = b.BlockHeight
                    WHERE b.Date >= '2018-01-01'
                    GROUP BY month
                    ORDER BY month;
                """
                
                # Query for _LND_DBReader_ChannelAnnouncements table.
                query_dbreader = """
                    SELECT DATE_FORMAT(b.Date, '%Y-%m') AS month, COUNT(*) AS count
                    FROM _LND_DBReader_ChannelAnnouncements a
                    JOIN Blockchain_Blocks b ON a.BlockIndex = b.BlockHeight
                    WHERE b.Date >= '2018-01-01'
                    GROUP BY month
                    ORDER BY month;
                """
                
                results_research = get_monthly_counts(cursor, query_research)
                results_dbreader = get_monthly_counts(cursor, query_dbreader)


                print("Monthly counts for _LNResearch_ChannelAnnouncements:")
                for row in results_research:
                    print(f"{row['month']}: {row['count']}")
                    data[row['month']] = {}
                    data[row['month']]["lnresearch"] = row['count']



                print("\nMonthly counts for _LND_DBReader_ChannelAnnouncements:")
                for row in results_dbreader:
                    print(f"{row['month']}: {row['count']}")
                    # Initialize the month entry if it doesn't exist
                    if row['month'] not in data:
                        data[row['month']] = {}
                    data[row['month']]["lnd_dbreader"] = row['count']
        return data





    def plot_data(self, data, xTicksShowEndsWith, xTicksToExclude):
        # Prepare data
        months = sorted(data.keys())  # Sort months for proper chronological order
        lnresearch_data = [data[month].get("lnresearch", 0) for month in months]
        lnd_dbreader_data = [data[month].get("lnd_dbreader", 0) for month in months]
        
        # Convert month strings to datetime objects for proper axis formatting
        x_data = [datetime.strptime(f"{month}-01", '%Y-%m-%d') for month in months]
        
        # Create folder path
        folderPath = f'/DATA/GENERATED/Compare_Sources/Channel_Announcements'
        folderPath += f'/{"20XX"+xTicksShowEndsWith}'
        
        # Initialize Chart Generator
        chart_generator = BaseChartGenerator(
            x_data=x_data,
            y_data_list=[lnresearch_data, lnd_dbreader_data],
            labels=["LNResearch", "LND DBReader"]
        )
        
        # Set smaller font size for y-axis label
        chart_generator.y_label_fontsize = 18
        
        chart_generator.customize_axes(
            x_label='Time',
            y_label='Channel Announcements Count',
            title='Comparison of Channel Announcements Sources Over Time'
        )
        chart_generator.set_x_ticks(ends_with=xTicksShowEndsWith, exclude_ends_with=xTicksToExclude)
        
        # Generate 10x6 chart
        chart_generator.generate_line_chart(figsize=(10, 6), print_header=True, print_footer=True)
        filePath = folderPath + f'/10x6_Full.svg'
        chart_generator.save_chart(filePath)
        print(f"[*] Saved: {filePath}")
        
        # Clean Up Memory
        gc.collect()