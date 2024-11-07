from matplotlib.ticker import PercentFormatter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import io
import os
from datetime import datetime
from typing import List, Dict, Any, Optional



class BaseChartGenerator:
    title_fontsize = 15
    x_label_fontsize = 24
    y_label_fontsize = 24
    tick_label_fontsize = 15
    legend_fontsize = 15
    footer_fontsize = 10


    def __init__(self, x_data, y_data_list, labels):
        # Save variables
        self.x_data = x_data
        self.y_data_list = y_data_list
        self.labels = labels
        self.x_ticks = None



    def customize_axes(self, x_label: str, y_label: str, title=None, x_formatter=None, y_formatter=None,
                        x_lim=None, y_lim=None, x_ticks=None, y_ticks=None, grid: bool = True):
        """
        Customize the axes of the chart.

        This method allows you to set various properties of the chart's axes, including labels, title, formatters, limits,
        ticks, and grid visibility. It provides flexibility in customizing the appearance and behavior of the chart's axes.

        Parameters:
        - x_label (str): The label for the x-axis.
        - y_label (str): The label for the y-axis.
        - title (str, optional): The title of the chart. Default is None.
        - x_formatter (Formatter, optional): A formatter for the x-axis. Default is None.
        - y_formatter (Formatter, optional): A formatter for the y-axis. Default is None.
        - x_lim (tuple, optional): A tuple specifying the limits for the x-axis (min, max). Default is None.
        - y_lim (tuple, optional): A tuple specifying the limits for the y-axis (min, max). Default is None.
        - x_ticks (list, optional): A list of specific tick values to be set on the x-axis. Default is None.
        - y_ticks (list, optional): A list of specific tick values to be set on the y-axis. Default is None.
        - grid (bool, optional): A boolean indicating whether to display grid lines. Default is True.

        Behavior:
        - If y-axis limits (`y_lim`) are not provided, the method will dynamically determine the limits based on the
          minimum and maximum values of the y_data_list, with some padding applied.
        - The method sets the provided title, labels, formatters, limits, and ticks for the chart's axes.
        - If grid is set to True, grid lines will be displayed on the chart.

        Example usage:
        ```
        chart_generator.customize_axes(
            x_label='Time',
            y_label='Value',
            title='Sample Chart',
            x_formatter=mdates.DateFormatter('%Y-%m-%d'),
            y_formatter=PercentFormatter(),
            x_lim=(datetime(2020, 1, 1), datetime(2023, 1, 1)),
            y_lim=(0, 100),
            x_ticks=['2020-01-01', '2021-01-01', '2022-01-01'],
            y_ticks=[0, 25, 50, 75, 100],
            grid=True
        )
        ```
        """

        # If y axis limits are not set, then find min and max values for y_data and apply some padding
        if y_lim is None:
            self.y_lim = self._find_y_lim_dynamically(self.y_data_list)

        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_formatter = x_formatter
        self.y_formatter = y_formatter
        self.x_lim = x_lim
        self.y_ticks = y_ticks
        self.grid = grid

        # Determine y-axis limits
        if y_lim is None:
            self.y_lim = self._find_y_lim_dynamically(self.y_data_list)
        else:
            self.y_lim = y_lim



    def set_x_ticks(self, ends_with=None, x_ticks=None):
        """
        Set the x-axis ticks for the chart.

        This method allows you to customize the x-axis ticks by either providing specific tick values or by specifying
        a pattern that the tick values should end with. If both `x_ticks` and `ends_with` are provided, `x_ticks` will
        take precedence.

        Parameters:
        - ends_with (str, optional): A string pattern that the x-axis tick values should end with. For example, if 
          `ends_with` is "-03-01", the x-axis will have ticks at dates ending with "-03-01".
        - x_ticks (list, optional): A list of specific tick values to be set on the x-axis. If provided, this will 
          override the `ends_with` parameter.

        Behavior:
        - If `x_ticks` is provided, it will be used directly to set the x-axis ticks.
        - If `ends_with` is provided, the method will filter the `x_data` to find dates that match the pattern specified
          by `ends_with`.
        - The first and last dates in `x_data` will always be included in the x-axis ticks to ensure the full range of 
          data is represented.

        Example usage:
        ```
        chart_generator.set_x_ticks(ends_with="-03-01")
        chart_generator.set_x_ticks(x_ticks=["2020-01-01", "2021-01-01"])
        ```
        """

        if x_ticks:
            self.x_ticks = x_ticks

        elif ends_with:
            self.x_ticks = [
                date for date in self.x_data
                if date.strftime('%Y-%m-%d').endswith(ends_with)
            ]

            # Add first date if not already in x_ticks
            if self.x_data[0] not in self.x_ticks and ends_with != "-03-01":
                self.x_ticks.insert(0, self.x_data[0])

            # Add last date if not already in x_ticks
            if self.x_data[-1] not in self.x_ticks:
                self.x_ticks.append(self.x_data[-1])



    def _customize_axes(self):
        if self.x_label:
            self.ax.set_xlabel(self.x_label, fontsize=self.x_label_fontsize)
        if self.y_label:
            self.ax.set_ylabel(self.y_label, fontsize=self.y_label_fontsize)
        if self.x_formatter:
            self.ax.xaxis.set_major_formatter(self.x_formatter)
        if self.y_formatter:
            self.ax.yaxis.set_major_formatter(self.y_formatter)
        if self.x_lim:
            self.ax.set_xlim(*self.x_lim)
        if self.y_lim:
            self.ax.set_ylim(*self.y_lim)
        
        self.ax.tick_params(axis='both', which='major', labelsize=self.tick_label_fontsize)
        
        if self.x_ticks is not None:
            # Ensure x_ticks are in the same format as x_data
            if isinstance(self.x_data[0], datetime):
                self.x_ticks = [datetime.strptime(tick, '%Y-%m-%d') if isinstance(tick, str) else tick for tick in self.x_ticks]
            self.ax.set_xticks(self.x_ticks)
            # Optionally set labels
            self.ax.set_xticklabels([tick.strftime('%Y-%m-%d') for tick in self.x_ticks], fontsize=self.tick_label_fontsize)
        
        if self.y_ticks is not None:
            self.ax.set_yticks(self.y_ticks)
            self.ax.set_yticklabels(self.y_ticks, fontsize=self.tick_label_fontsize)
        
        if self.grid:
            self.ax.grid(True)
        self.fig.tight_layout()



    def _find_y_lim_dynamically(self, y_data_list):
        '''
        Finds min and max values for y_data and applies some padding.

        Returns tuple of (overall_y_min, overall_y_max)
        '''
        overall_y_min = float('inf')
        overall_y_max = float('-inf')

        # Iterate over each y_data to find the overall min and max
        if y_data_list:
            for y_data in y_data_list:
                current_y_min = min(y_data) - (0.02 * (max(y_data) - min(y_data)))
                current_y_max = max(y_data) + (0.25 * (max(y_data) - min(y_data)))
                # current_y_max = max(y_data) + (0.12 * (max(y_data) - min(y_data)))

                # Update overall min and max
                overall_y_min = min(overall_y_min, current_y_min)
                overall_y_max = max(overall_y_max, current_y_max)

        # If overall min Y is near 0, then set it to 0
        if overall_y_min < 0.2 * overall_y_max:
            overall_y_min = 0

        return (overall_y_min, overall_y_max)



    def _add_footer_texts(self):
        self.fig.text(0.99, 0.01, '© Vilnius university Kaunas faculty', ha='right', fontsize=self.footer_fontsize)
        self.fig.text(0.01, 0.01, 'Updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ha='left', fontsize=self.footer_fontsize)



    def generate_line_chart(self, figsize=None, print_header=True, print_footer=True):
        """
        Generates a line chart with one or multiple lines.

        :param figsize: Figure size tuple (width, height)
        :param print_header: Whether to print the header (default: True)
        :param print_footer: Whether to print the footer (default: True)
        :return: BytesIO object containing the chart image
        """

        with plt.rc_context({'text.usetex': True, 'font.family': 'serif'}):
            
            # Setup plot
            self.figsize = figsize
            self.fig, self.ax = plt.subplots(figsize=self.figsize)

            self.ax.margins(x=0.01, y=0)

            # Add Header Title
            if self.title and print_header:
                self.ax.set_title(self.title, fontsize=self.title_fontsize)

            # Plot each line
            for y_data, label in zip(self.y_data_list, self.labels):
                self.ax.plot(self.x_data, y_data, label=label)

            # Add legend
            if(self.figsize == (6, 6)):
                self.ax.legend(loc='upper left', fontsize=self.legend_fontsize)
            else:
                self.ax.legend(loc='upper left', fontsize=self.legend_fontsize)

            # Customize axes
            self._customize_axes()

            # Rotate date labels for clarity
            self.fig.autofmt_xdate()

            # Add "Updated" and copyright texts
            if print_footer:
                self._add_footer_texts()

            # Adjust layout to minimize gaps
            gap_bottom = 0.03 if print_footer else 0.0
            self.fig.tight_layout(rect=[0, gap_bottom, 1, 1])

            # Save the chart to a virtual file
            self.virtual_file = self.get_virtual_file()

            return self.virtual_file



    def get_virtual_file(self):
        virtual_file = io.BytesIO()
        # self.fig.savefig(virtual_file, format='png', dpi=1000)
        self.fig.savefig(virtual_file, format='svg')
        plt.close(self.fig)
        virtual_file.seek(0)
        return virtual_file



    def save_chart(self, filename: str):
        """
        Saves the chart image to a file.

        :param filename: The filename to save the chart as
        :return: The path to the saved chart file
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(self.virtual_file.getbuffer())
        return filename








class LorenzCurveChartGenerator(BaseChartGenerator):
    x_label_fontsize = 20
    y_label_fontsize = 20


    def __init__(self, datasets=None, title=None, x_label=None, y_label=None):

        # Save variables
        # self.x_data = x_data
        # self.y_data_list = y_data_list
        # self.labels = labels
        self.x_ticks = None

        # Save Lorenz specific variables
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.datasets = datasets
        self.y_data_list = None




    def _plot_perfect_equality_line(self):
        plt.plot([0, 100], [0, 100], 'k--')

        # Force the plot to update transformations
        plt.draw()

        # Get axes limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Get axes size in display coordinates
        bbox = self.ax.get_window_extent().transformed(plt.gcf().dpi_scale_trans.inverted())
        width_display, height_display = bbox.width, bbox.height

        # Calculate the scaling factors
        xscale = width_display / (xlim[1] - xlim[0])
        yscale = height_display / (ylim[1] - ylim[0])

        # Compute the angle of the perfect equality line in display coordinates
        angle_rad = np.arctan2(yscale * (ylim[1] - ylim[0]), xscale * (xlim[1] - xlim[0]))
        angle_deg = np.degrees(angle_rad)

        # Place the text with the calculated angle
        self.ax.text(50, 55, 'Perfect Equality Line',
                rotation=angle_deg,
                ha='center', va='center',
                transform=self.ax.transData,
                fontsize=15)




    def generate_lorenz_curves(self, figsize=None, print_header=True, print_footer=True):
        """
        Generates Lorenz curves for one or multiple datasets.

        :param figsize: Figure size tuple (width, height)
        :param print_header: Whether to print the header (default: True)
        :param print_footer: Whether to print the footer (default: True)
        :return: BytesIO object containing the chart image
        """

        with plt.rc_context({'text.usetex': True, 'font.family': 'serif'}):
            # Setup plot
            self.figsize = figsize
            self.fig, self.ax = plt.subplots(figsize=self.figsize)


            self.ax.margins(x=0.01, y=0)

            # Add Header Title
            if self.title and print_header:
                self.ax.set_title(self.title, fontsize=self.title_fontsize)


            for data in self.datasets:
                percentiles = data['percentiles']
                cumulative_percentages = data['cumulative_percentages']
                label = data['label']
                plt.plot(percentiles, cumulative_percentages, label=label)


            # Customize axes
            self.customize_axes(
                x_label=self.x_label,
                y_label=self.y_label,
                title=self.title,
                x_formatter=PercentFormatter(),
                y_formatter=PercentFormatter(),
                x_lim=(0, 100),
                y_lim=(0, 100),
                grid=True
            )
            self._customize_axes()

            # Legend
            if(self.figsize == (6, 6)):
                plt.legend(loc='upper left', fontsize=11)
            else:
                plt.legend(loc='upper left', fontsize=self.legend_fontsize)
            
            # Add "Updated" and copyright texts
            if print_footer:
                self._add_footer_texts()

            # Adjust layout to minimize gaps
            gap_bottom = 0.03 if print_footer else 0.0
            self.fig.tight_layout(rect=[0, gap_bottom, 1, 1])

            # Draw perfect equality line
            self._plot_perfect_equality_line()

            # Save the chart to a virtual file
            self.virtual_file = self.get_virtual_file()

            return self.virtual_file




    def generate_example_lorenz_curve(self, figsize=None, print_header=True, print_footer=True):
        """
        Generates an example Lorenz curve with annotations.

        :param figsize: Figure size tuple (width, height)
        :return: BytesIO object containing the chart image
        """

        with plt.rc_context({'text.usetex': True, 'font.family': 'serif'}):

            # Setup plot
            self.figsize = figsize
            self.fig, self.ax = plt.subplots(figsize=self.figsize)

            # Lorenz curve example
            x_lorenz = np.linspace(0, 100, 100)
            y_lorenz = (x_lorenz / 100) ** 4 * 100
            self.ax.plot(x_lorenz, y_lorenz, label='Lorenz Curve', linewidth=3, color='black')

            # Fill areas
            self.ax.fill_between(x_lorenz, y_lorenz, x_lorenz, hatch='///\\\\\\', edgecolor='black', facecolor='white')
            self.ax.text(55, 35, 'Gini Coefficient', ha='center', va='center', fontsize=15,
                    bbox=dict(facecolor='white', alpha=1))
            self.ax.text(85, 70, 'A', ha='center', va='center', fontsize=25, bbox=dict(facecolor='white', alpha=1))

            self.ax.fill_between(x_lorenz, y_lorenz, hatch='++', edgecolor='black', facecolor='white')
            self.ax.text(85, 25, 'B', ha='center', va='center', fontsize=25, bbox=dict(facecolor='white', alpha=1))

            # Customize axes
            self.customize_axes(
                x_label='Cumulative Percentage of Population',
                y_label='Cumulative Percentage of Wealth',
                title='Lorenz Curve Example',
                x_formatter=PercentFormatter(),
                y_formatter=PercentFormatter(),
                x_lim=(0, 100),
                y_lim=(0, 100),
                grid=False
            )
            self._customize_axes()
            self.ax.legend(loc='upper left', fontsize=15)

            # Add "Updated" and copyright texts
            if print_footer:
                self._add_footer_texts()

            # Adjust layout to minimize gaps
            gap_bottom = 0.03 if print_footer else 0.0
            self.fig.tight_layout(rect=[0, gap_bottom, 1, 1])

            # Draw perfect equality line
            self._plot_perfect_equality_line()

            # Save the chart to a virtual file
            self.virtual_file = self.get_virtual_file()

            return self.virtual_file




