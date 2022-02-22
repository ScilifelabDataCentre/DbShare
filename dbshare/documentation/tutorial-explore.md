---
title: Explore an existing database
ordinal: 101
---

Public databases in DbShare can be explored without being logged in.
This tutorial uses a public database at the [SciLifeLab
instance of DbShare](https://dbshare.scilifelab.se/).

The [demo database](https://dbshare.scilifelab.se/db/demo)
contains the following:

- A table of flower measurements for specimens of three species of Iris:
  [iris_flower_measurements](https://dbshare.scilifelab.se/table/demo/iris_flower_measurements)
- A view selecting the measurements of one species from the table:
  [iris-setosa](https://dbshare.scilifelab.se/view/demo/iris-setosa)
- A table of some Dow Jones share index data:
  [dow_jones_index](https://dbshare.scilifelab.se/table/demo/dow_jones_index)
  A more complicated, real-world data set.

### Inspect the **iris** data

- Go to [iris_flower_measurements](https://dbshare.scilifelab.se/table/demo/iris_flower_measurements).
  (Use _ctrl-click_ or whatever method your browser has to bring up the table
  in a separate window or tab.)
- There are four columns of numerical data for the dimensions of the flower
  parts in centimeters. The fifth column shows the species of Iris.
- Inspect the schema for the table; click **Schema**. This shows the data type
  and constraints on the values in each column.
- This dataset was uploaded from a CSV file, so the schema was inferred from
  it. The numerical column data is encoded as real (floating point) values,
  while the **class** column contains text values.
- All columns are set as NOT NULL. This means that no rows may contain NULL
  values in any column. This is defined when the schema is created
- Click **Statistics**. This will compute a number of simple statistics for
  the values of each column, such as:
    * mean, median and standard deviation for numerical columns,
    * whether there are any NULL values in a column,
    * the number of unique values in a column,
    * list the unique values, if there are less than 8 of them.

### Query the iris data

- Go back to the page for **Database demo** (in the menu at the top of the
  page).
- Click **Query**. The page contains input fields for the usual parts of an
  ordinary SQL query statement beginning with **`SELECT`**.
- To the right are panes with information on the columns of each table and view
  in the database, to aid formulating a query.
- Fill in the fields to produce the SQL statement, and click **Execute query**:

    - **`SELECT`** sepal_width, sepal_length
    - **`FROM`** iris_flower_measurements
    - **`WHERE`** class='Iris-setosa' _(NOTE: Sensitive to character case!)_
    - **`LIMIT`** 200 _(this is default)_

- The result page shows the complete SQL query at the top, with the number
  of selected rows, and then the row values below.
- Click **Edit query**.
- Try changing the query in different ways, adding or modifying parts to
  the SQL. If the SQL statement becomes invalid, an error message will be
  produced.

### Explore the view

A **view** in SQL is a saved query that has been given a name, and
which looks like a table. When it is accessed, it automatically
recomputes the query and produces the result as if it were a table.

On the [demo database](https://dbshare.scilifelab.se/db/demo) page,
there is a view **iris-setosa** defined. Check it out.
