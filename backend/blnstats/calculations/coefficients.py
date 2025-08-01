import numpy as np
import math
from datetime import datetime
from ..data_types import VerticesAspectDataStructure, CoefficientsDataStructure





class Coefficients:
    """
    Class for calculating various centralization and decentralization coefficients.

    This class provides methods to compute different statistical measures that help
    assess the degree of centralization or decentralization in a network, for example
    analyzing BLN node capacities or channel distributions.

    Coefficients calculated:
    1. Gini Coefficient: Measures inequality (0.0 - Decentralized, 1.0 - Centralized)
    2. Herfindahl-Hirschman Index (HHI): Measures market concentration (0.0 - Decentralized, 10000.0 - Centralized)
    3. Theil Index: Measures inequality with sensitivity to differences (0.0 - Decentralized, Higher - More Centralized)
    4. Normalized Theil Index: Theil Index normalized to [0, 1] range
    5. Shannon Entropy: Measures diversity and unpredictability (0.0 - Centralized, Higher - More Decentralized)
    6. Normalized Shannon Entropy: Shannon Entropy normalized to [0, 1] range
    7. Nakamoto Coefficient: Measures minimum entities to reach 51% of the total (1 - Centralized, Higher - More Decentralized)
    8. Top 10 Percent Control Total Percentage: Measures percentage of the total network that top 10% of the nodes/entities have control over
    9. Top 10 Percent Control Sum: Measures sum of values that top 10% of the nodes/entities have

    Each method takes a list of non-negative integer values representing nodes/entities capacities
    or channel counts and returns the corresponding coefficient value.
    """



    def calculate_gini(self, data: list) -> float:
        """
        Calculate the Gini Coefficient for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Gini value (0.0 - Decentralized, 1.0 - Centralized)
        """
        n = len(data)
        if n == 0:
            return 0.0

        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        sorted_data = np.sort(data)
        sum_data = np.sum(sorted_data)
        if sum_data == 0:
            return 0.0  # All values are zero; Gini is not defined, so return 0

        index = np.arange(1, n + 1)
        gini_numerator = np.sum((2 * index - n - 1) * sorted_data)
        gini_denominator = n * sum_data
        gini = gini_numerator / gini_denominator
        return gini
    


    def calculate_hhi(self, data: list) -> float:
        """
        Calculate the Herfindahl-Hirschman Index (HHI) for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - HHI value (0.0 - Decentralized, 10000.0 - Centralized)
        """
        total = sum(data)
        if total == 0:
            return 0.0

        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        shares = data / total
        hhi = np.sum(shares ** 2) * 10000
        return hhi
    


    def calculate_theil_index(self, data: list) -> float:
        """
        Calculate the Theil Index for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Theil Index value (0.0 - Decentralized, Higher Value - More Centralized)
        """
        n = len(data)
        total = sum(data)
        if n == 0 or total == 0:
            return 0.0

        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        shares = data / total
        shares = shares[shares > 0]  # Exclude zero shares to avoid log(0)

        theil = np.sum(shares * np.log(shares * n))
        return theil



    def calculate_max_theil_index(self, n: int) -> float:
        """
        Calculate the maximum possible Theil Index for n elements.

        :param n: int - Number of elements
        :return: float - Maximum Theil Index value
        """
        if n <= 1:
            return 0.0
        return math.log(n)



    def calculate_normalized_theil_index(self, data) -> float:
        """
        Calculate the Normalized Theil Index for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Normalized Theil Index value (0.0 - Decentralized, 1.0 - Centralized)
        """
        theil_index = self.calculate_theil_index(data)
        max_theil = self.calculate_max_theil_index(len(data))
        if max_theil == 0:
            return 0.0

        coefficient_value = theil_index / max_theil
        return coefficient_value



    def calculate_shannon_entropy(self, data) -> float:
        """
        Calculate the Shannon Entropy Index for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Shannon Entropy value (0.0 - Centralized, Higher Value - More Decentralized)
        """
        total = sum(data)
        if total == 0:
            return 0.0

        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        shares = data / total
        shares = shares[shares > 0]  # Exclude zero shares to avoid log(0)

        entropy = -np.sum(shares * np.log2(shares))
        return entropy



    def calculate_max_shannon_entropy(self, n) -> float:
        """
        Calculate the maximum possible Shannon Entropy for n elements.

        :param n: int - Number of elements
        :return: float - Maximum Shannon Entropy value
        """
        if n <= 1:
            return 0.0
        return math.log2(n)



    def calculate_normalized_shannon_entropy(self, data) -> float:
        """
        Calculate the Normalized Shannon Entropy Index for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Normalized Shannon Entropy value (0.0 - Centralized, 1.0 - Decentralized)
        """
        shannon_entropy = self.calculate_shannon_entropy(data)
        max_entropy = self.calculate_max_shannon_entropy(len(data))
        if max_entropy == 0:
            return 0.0

        coefficient_value = shannon_entropy / max_entropy
        return coefficient_value



    def calculate_nakamoto(self, data) -> int:
        """
        Calculate the Nakamoto Coefficient for the given data.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: int - Nakamoto Coefficient value (1 - Centralized, Higher Value - More Decentralized)
        """
        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        total = np.sum(data)
        if total == 0:
            return 0  # No capacity; Nakamoto coefficient is undefined

        sorted_data = np.sort(data)[::-1]  # Sort in descending order
        cumulative_share = np.cumsum(sorted_data) / total

        # Find the smallest number of nodes that cumulatively have more than 51% share
        nodes_needed = np.searchsorted(cumulative_share, 0.51) + 1
        return nodes_needed



    def calculate_top_10_percent_control_percentage(self, data) -> float:
        """
        Calculate percentage of the total network that top 10% of the nodes/entities have control over.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Percentage of the total network that top 10% of the nodes/entities have control over
        """
        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        # Sort in descending order using [::-1]
        sorted_data = np.sort(data)[::-1]
        ten_percent_index = int(0.1 * len(sorted_data))
        return np.sum(sorted_data[:ten_percent_index]) / np.sum(sorted_data)
    


    def calculate_top_10_percent_control_sum(self, data) -> float:
        """
        Calculate sum of values that top 10% of the nodes/entities have.

        :param data: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :return: float - Sum of values that top 10% of the nodes/entities have
        """
        data = np.array(data, dtype=np.float64)
        if np.any(data < 0):
            raise ValueError("All data values must be non-negative.")

        # Sort in descending order using [::-1]
        sorted_data = np.sort(data)[::-1]
        ten_percent_index = int(0.1 * len(sorted_data))
        return np.sum(sorted_data[:ten_percent_index])



    def calculate_coefficient(self, values: list, coefficient_type: str) -> float:
        """
        Calculate the coefficient for the given values and coefficient type.

        :param values: List[int] - Array of non-negative integer values representing nodes/entities capacities or channel counts
        :param coefficient_type: str - Type of coefficient to calculate
        :return: float - Coefficient value
        """
        if coefficient_type == "Gini":
            return self.calculate_gini(values)
        elif coefficient_type == "HHI":
            return self.calculate_hhi(values)
        elif coefficient_type == "Theil":
            return self.calculate_theil_index(values)
        elif coefficient_type == "NormalizedTheil":
            return self.calculate_normalized_theil_index(values)
        elif coefficient_type == "ShannonEntropy":
            return self.calculate_shannon_entropy(values)
        elif coefficient_type == "NormalizedShannonEntropy":
            return self.calculate_normalized_shannon_entropy(values)
        elif coefficient_type == "Nakamoto":
            return self.calculate_nakamoto(values)
        elif coefficient_type == "Top10PercentControlPercentage":
            return self.calculate_top_10_percent_control_percentage(values)
        elif coefficient_type == "Top10PercentControlSum":
            return self.calculate_top_10_percent_control_sum(values)
        else:
            raise ValueError(f"Invalid coefficient type: {coefficient_type}")




    def calculate_on_vertices_data(self, vertices_data: VerticesAspectDataStructure, coefficient_type: str) -> CoefficientsDataStructure:
        """
        Calculate the Gini Coefficient for the given vertices aspect data and return it in coefficients structure.

        :param vertices_data: VerticesAspectDataStructure - Data structure containing node capacities or channel counts
        :param coefficient_type: str - Type of coefficient to calculate
        :return: CoefficientsDataStructure - Structure containing coefficient values for each block height
        """


        # Calculate the coefficient for each block height
        coefficient_data = {}
        for block_height, vertice_entry in vertices_data.data.items():
            date = vertice_entry.date
            timestamp = vertice_entry.timestamp
            values = [vertice.value for vertice in vertice_entry.vertices]
            coefficient_value = self.calculate_coefficient(values, coefficient_type)
            coefficient_data[block_height] = {
                "value": coefficient_value,
                "date": date,
                "timestamp": timestamp
            }



        # Formulate the description of the data for the meta section
        input_y_axis = vertices_data.meta.yAxis.split("(")[1].split(")")[0]
        input_subject, input_metric = input_y_axis.split(",")

        SUBJECT_MAPPING = {
            "NodeID": "nodes",
            "EntityName": "entities"
        }
        METRIC_MAPPING = {
            "Capacity": "capacities",
            "ChannelCount": "channel counts"
        }

        subjectOfAnalysis = SUBJECT_MAPPING.get(input_subject, "UNKNOWN SUBJECT")
        analysisMetric = METRIC_MAPPING.get(input_metric, "UNKNOWN METRIC")



        # Pass through the yAxisSupplyChain and append the input yAxis
        yAxisSupplyChain = vertices_data.meta.yAxisSupplyChain.copy()
        yAxisSupplyChain.append(vertices_data.meta.yAxis)



        # Return the coefficients data structure
        return CoefficientsDataStructure(
            meta={
                "type": f"CoefficientsAcrossTheTime({coefficient_type})",
                "description": f"{coefficient_type} Coefficients for {subjectOfAnalysis} {analysisMetric} at given block heights",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "xAxis": "BlockHeight",
                "yAxis": coefficient_type,
                "yAxisSupplyChain": yAxisSupplyChain
            },
            data={block_height: CoefficientsDataStructure.CoefficientData(
                value=coefficient_data[block_height]["value"],
                date=coefficient_data[block_height]["date"],
                timestamp=coefficient_data[block_height]["timestamp"],
                input_array_length=len(vertices_data.data[block_height].vertices),
                input_array_sum=sum([vertice.value for vertice in vertices_data.data[block_height].vertices])
            ) for block_height in coefficient_data.keys()}
        )




