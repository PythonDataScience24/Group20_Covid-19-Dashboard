# Unit tests - unexpected outputs

### test_class_initialization

Test that no data is loaded after simply creating an instance 
of `data_prep.DataProcessor`

### test_data_initialization

After calling `self.init_data()`, the dataframes `df_absolute`
and `df_normalized` may have an incorrect number of rows, which
would be an unexpected output, meaning that the data import 
failed in some way.

### test_deaths_per_cases

A smoke test - deaths per cases must be positive.

### test_preprocess_data

Test that unnecessary columns have been dropped.