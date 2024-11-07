import datetime
import matplotlib.dates as mdates
from ..database.raw_data_selector import RawDataSelector
from ..charts.chart_generator import ChartGenerator

class GiniChartWorkflow:


    def __init__(self):
        self.raw_data_selector = RawDataSelector()
        self.chart_generator = ChartGenerator()



    def generate_gini_chart(self, dataset_type: str):
        """
        Generates a Gini coefficient chart for the given dataset_type.

        :param dataset_type: 'ginichannelcountbynodes' or 'giniliquiditybynodes'
        :return: BytesIO object containing the chart image
        """
        
        # Step 1: Fetch data
        data = self.raw_data_selector.get_gini_data(dataset_type)
        dates = [datetime.datetime.strptime(line[0], '%Y-%m-%d') for line in data]
        gini_values = [line[1] for line in data]



        # Step 2: Set up parameters for the chart
        title_map = {
            'ginichannelcountbynodes': 'Gini coefficient of degree\ncentrality (BLN Nodes)',
            'giniliquiditybynodes': 'Gini coefficient of weighted degree\ncentrality (BLN Nodes)'
        }
        title = title_map.get(dataset_type, 'Gini Coefficient')
        x_label = 'Time'
        y_label = 'Gini Coefficient'

        # Customize x-axis
        x_formatter = mdates.DateFormatter('%Y-%m-%d')
        x_locator = mdates.YearLocator()

        # y-axis limits
        y_lim = (0.79, 1.0)

        # x-ticks on a specific day of the year (e.g., June 1st)
        day_of_year = '-06-01'
        xticks = [date for date in dates if date.strftime('-%m-%d') == day_of_year]



        # Step 3: Generate chart
        chart_image = self.chart_generator.generate_line_chart(
            x_data=dates,
            y_data_list=[gini_values],
            labels=['Gini Coefficient'],
            x_label=x_label,
            y_label=y_label,
            title=title,
            x_formatter=x_formatter,
            x_locator=x_locator,
            y_lim=y_lim,
            x_ticks=xticks,
            rotate_x_ticks=True,
            grid=True,
            figsize=(4, 6)
        )
        return chart_image




