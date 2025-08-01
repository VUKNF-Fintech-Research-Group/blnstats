import unittest
import math
from blnstats.calculations.coefficients import Coefficients

class TestCoefficients(unittest.TestCase):

    def setUp(self):
        self.coefficients = Coefficients()



    def test_calculate_gini(self):
        # Uniform distribution (Gini should be 0)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_gini(data_uniform)
        self.assertAlmostEqual(result, 0.0, places=5)

        # Single entity holds all value (Gini should be 0.75)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_gini(data_centralized)
        self.assertAlmostEqual(result, 0.75, places=5)

        # Mixed values
        data_mixed = [5, 15, 25, 55]
        result = self.coefficients.calculate_gini(data_mixed)
        expected_result = 0.4  # Calculated manually or from a reliable source
        self.assertAlmostEqual(result, expected_result, places=5)

        # Empty data
        data_empty = []
        result = self.coefficients.calculate_gini(data_empty)
        self.assertEqual(result, 0.0)

        # All zeros
        data_zeros = [0, 0, 0, 0]
        result = self.coefficients.calculate_gini(data_zeros)
        self.assertEqual(result, 0.0)

        # Negative values (should raise ValueError)
        data_negative = [10, -5, 15]
        with self.assertRaises(ValueError):
            self.coefficients.calculate_gini(data_negative)



    def test_calculate_hhi(self):
        # Uniform distribution (HHI should be minimum)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_hhi(data_uniform)
        expected_result = 2500.0  # (1/n) * 10000
        self.assertAlmostEqual(result, expected_result, places=5)

        # Single entity holds all value (HHI should be 10000)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_hhi(data_centralized)
        self.assertEqual(result, 10000.0)

        # Mixed values
        data_mixed = [5, 15, 25, 55]
        result = self.coefficients.calculate_hhi(data_mixed)
        expected_result = 3900.0  # Calculated manually or from a reliable source
        self.assertAlmostEqual(result, expected_result, places=0)

        # Empty data
        data_empty = []
        result = self.coefficients.calculate_hhi(data_empty)
        self.assertEqual(result, 0.0)

        # All zeros
        data_zeros = [0, 0, 0, 0]
        result = self.coefficients.calculate_hhi(data_zeros)
        self.assertEqual(result, 0.0)

        # Negative values (should raise ValueError)
        data_negative = [10, -5, 15]
        with self.assertRaises(ValueError):
            self.coefficients.calculate_hhi(data_negative)



    def test_calculate_theil_index(self):
        # Uniform distribution (Theil Index should be 0)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_theil_index(data_uniform)
        self.assertAlmostEqual(result, 0.0, places=5)

        # Single entity holds all value (Theil Index should be max)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_theil_index(data_centralized)
        max_theil = self.coefficients.calculate_max_theil_index(len(data_centralized))
        self.assertAlmostEqual(result, max_theil, places=5)

        # Mixed values
        data_mixed = [5, 15, 25, 55]
        result = self.coefficients.calculate_theil_index(data_mixed)
        expected_result = 0.2766  # Approximate value
        self.assertAlmostEqual(result, expected_result, places=3)

        # Empty data
        data_empty = []
        result = self.coefficients.calculate_theil_index(data_empty)
        self.assertEqual(result, 0.0)

        # All zeros
        data_zeros = [0, 0, 0, 0]
        result = self.coefficients.calculate_theil_index(data_zeros)
        self.assertEqual(result, 0.0)

        # Negative values (should raise ValueError)
        data_negative = [5, -10, 15]
        with self.assertRaises(ValueError):
            self.coefficients.calculate_theil_index(data_negative)



    def test_calculate_normalized_theil_index(self):
        # Uniform distribution (Normalized Theil Index should be 0)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_normalized_theil_index(data_uniform)
        self.assertAlmostEqual(result, 0.0, places=5)

        # Single entity holds all value (Normalized Theil Index should be 1)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_normalized_theil_index(data_centralized)
        self.assertAlmostEqual(result, 1.0, places=5)



    def test_calculate_shannon_entropy(self):
        # Uniform distribution (Entropy should be maximum)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_shannon_entropy(data_uniform)
        max_entropy = self.coefficients.calculate_max_shannon_entropy(len(data_uniform))
        self.assertAlmostEqual(result, max_entropy, places=5)

        # Single entity holds all value (Entropy should be 0)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_shannon_entropy(data_centralized)
        self.assertAlmostEqual(result, 0.0, places=5)

        # Mixed values
        data_mixed = [5, 15, 25, 55]
        result = self.coefficients.calculate_shannon_entropy(data_mixed)
        expected_result = 1.601  # Approximate value
        self.assertAlmostEqual(result, expected_result, places=3)

        # Empty data
        data_empty = []
        result = self.coefficients.calculate_shannon_entropy(data_empty)
        self.assertEqual(result, 0.0)

        # All zeros
        data_zeros = [0, 0, 0, 0]
        result = self.coefficients.calculate_shannon_entropy(data_zeros)
        self.assertEqual(result, 0.0)



    def test_calculate_normalized_shannon_entropy(self):
        # Uniform distribution (Normalized Entropy should be 1)
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_normalized_shannon_entropy(data_uniform)
        self.assertAlmostEqual(result, 1.0, places=5)

        # Single entity holds all value (Normalized Entropy should be 0)
        data_centralized = [0, 0, 0, 100]
        result = self.coefficients.calculate_normalized_shannon_entropy(data_centralized)
        self.assertAlmostEqual(result, 0.0, places=5)



    def test_calculate_nakamoto(self):
        # Uniform distribution (Nakamoto Coefficient should be ceil(0.51 * n))
        data_uniform = [10, 10, 10, 10]
        result = self.coefficients.calculate_nakamoto(data_uniform)
        expected_result = 3  # 3 nodes needed to reach over 51%
        self.assertEqual(result, expected_result)

        # Single entity holds all value (Nakamoto Coefficient should be 1)
        data_centralized = [100, 0, 0, 0]
        result = self.coefficients.calculate_nakamoto(data_centralized)
        self.assertEqual(result, 1)

        # Mixed values
        data_mixed = [55, 25, 15, 5]
        result = self.coefficients.calculate_nakamoto(data_mixed)
        self.assertEqual(result, 1)

        # All zeros (Nakamoto Coefficient should be 0)
        data_zeros = [0, 0, 0, 0]
        result = self.coefficients.calculate_nakamoto(data_zeros)
        self.assertEqual(result, 0)

        # Empty data (Nakamoto Coefficient should be 0)
        data_empty = []
        result = self.coefficients.calculate_nakamoto(data_empty)
        self.assertEqual(result, 0)

        # Negative values (should raise ValueError)
        data_negative = [10, -5, 15]
        with self.assertRaises(ValueError):
            self.coefficients.calculate_nakamoto(data_negative)



    def test_calculate_max_theil_index(self):
        # n <= 1 should return 0
        result = self.coefficients.calculate_max_theil_index(1)
        self.assertEqual(result, 0.0)

        # n > 1
        result = self.coefficients.calculate_max_theil_index(4)
        expected_result = math.log(4)
        self.assertAlmostEqual(result, expected_result, places=5)

    def test_calculate_max_shannon_entropy(self):
        # n <= 1 should return 0
        result = self.coefficients.calculate_max_shannon_entropy(1)
        self.assertEqual(result, 0.0)

        # n > 1
        result = self.coefficients.calculate_max_shannon_entropy(4)
        expected_result = math.log2(4)
        self.assertAlmostEqual(result, expected_result, places=5)



if __name__ == '__main__':
    unittest.main()
