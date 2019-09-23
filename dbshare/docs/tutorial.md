### Exploring databases using DbShare

Public databases in DbShare can be explored without having an account
in the system. This tutorial uses a public database at the [SciLifeLab
instance of DbShare](https://dbshare.scilifelab.se/).

The the [demo database](https://dbshare.scilifelab.se/db/demo)
contains the following:

- A table of flower measurements for specimens of three species of Iris:
  [iris_flower_measurements](https://dbshare.scilifelab.se/table/demo/iris_flower_measurements)
- A view selecting the measurements of one species from the table:
  [iris-setosa](https://dbshare.scilifelab.se/view/demo/iris-setosa)
- A table of some Dow Jones share index data: [dow_jones_index](https://dbshare.scilifelab.se/table/demo/dow_jones_index)

#### Inspect the Iris data

- Go to [iris_flower_measurements](https://dbshare.scilifelab.se/table/demo/iris_flower_measurements).
  (Use your browser to bring up the table in a separate   window or tab.)
- There are four columns of numerical data for the dimensions of the flower
  parts in centimeters. The fifth column shows the species of Iris.
- Inspect the schema for the table; click **Schema**.
- This dataset was uploaded from a CSV file, so the schema was inferred from
  it. The numerical data is encoded as real (floating point) values, while the
  class is a text value.
- All columns are set as NOT NULL since the input file contained values in
  all cells of the rows for all columns.
- Click **Statistics**. This will compute a number of simple statistics for
  the values of each column, such as:
    * mean, median and standard deviation for numerical columns,
    * whether there are any NULL values in a column,
    * the number of unique values in a column,
    * list the unique values, if there are less than 8 of them.

#### Query the Iris data

- Go back to the page for **Database demo** (in the menu at the top of the
  page).
- Click **Query**. The page contains input fields for the usual parts of an
  ordinary SQL query statement beginning with "SELECT...".
- To the right are panes with information on the columns of each table and view
  in the database, to aid formulating a query.
- Fill in the fields to produce the SQL statement `SELECT `: