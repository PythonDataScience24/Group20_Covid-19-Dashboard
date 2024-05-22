# Unit tests - unexpected outputs

### test_data_initialization(self)

After calling `self.init_data()`, the dataframes `df_absolute`
and `df_normalized` may have an incorrect number of rows, which
would be an unexpected output, meaning that the data import 
failed in some way.
