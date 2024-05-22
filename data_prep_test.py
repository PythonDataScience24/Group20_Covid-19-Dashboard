import unittest
from data_prep import DataProcessor


class DataPrepTest(unittest.TestCase):
    def setUp(self):
        self.data_processor = DataProcessor()

    def init_data(self):
        self.data_processor.initialize_data('Country')
        return self.data_processor.get_data()

    def test_class_initialization(self):
        # test that the __init__(self) method in DataProcessor
        # doesn't load any data
        self.assertIsNone(self.data_processor.df_abs)
        self.assertIsNone(self.data_processor.df_norm)

    def test_data_initialization(self):
        df_absolute, df_normalized = self.init_data()
        expected_row_count = 47712
        self.assertEqual(len(df_absolute.index), expected_row_count)
        self.assertEqual(len(df_normalized.index), expected_row_count)
        self.assertTrue('deaths_per_cases' in df_absolute.columns)

    def test_deaths_per_cases(self):
        df_absolute, df_normalized = self.init_data()
        self.assertTrue(df_absolute['deaths_per_cases'].min() >= 0)

    def test_preprocess_data(self):
        df_absolute, df_normalized = self.init_data()
        self.assertTrue('Country' in  df_absolute.columns)
        # test that unnecessary columns have been dropped
        self.assertFalse('alpha-3' in  df_absolute.columns)
        self.assertFalse('alpha-2' in  df_absolute.columns)
        self.assertFalse('2019 [YR2019]' in  df_absolute.columns)
        self.assertFalse('2020 [YR2020]' in  df_absolute.columns)
        self.assertFalse('2021 [YR2021]' in  df_absolute.columns)
        self.assertFalse('Country Code' in  df_absolute.columns)


if __name__ == '__main__':
    unittest.main()