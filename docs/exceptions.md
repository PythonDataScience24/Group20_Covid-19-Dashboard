# Exception Handling Rationale

### FileNotFoundError

- **Description**: This exception is raised when the CSV files required by the application are not found in the specified directory.
- **Handling**: We catch this exception and provide a user-friendly message indicating the missing files. We then initialize the dataframes as empty to allow the application to continue running.
- 
### pd.errors.EmptyDataError

- **Description**: This exception occurs if the CSV files are found but are empty.
- **Handling**: We catch this exception and notify the user that the files are empty, initializing the dataframes as empty to avoid further errors.

### General Exception

- **Description**: This is a catch-all for any other unexpected exceptions that may occur.
- **Handling**: We catch any other exceptions, log the error message, and initialize the dataframes as empty to prevent the application from crashing.
