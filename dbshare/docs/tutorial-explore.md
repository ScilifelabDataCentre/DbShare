# Tutorial: Explore a database

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

#### Inspect the iris data

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

#### Query the iris data

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

### Explore the saved charts

On the [demo database](https://dbshare.scilifelab.se/db/demo) page,
there are a couple of items **sepals** and **petals** under the
**iris_flower_measurements** table entry. These are saved charts 
visualizing data in that table.

A chart is dynamic in the sense that each time it is accessed, the data it
relies on is fetched anew from the database and re-rendered. This means
that one can rely on the chart always being up-to-date with the data
at the time the page is rendered.

Charts can show data from either a table or a view. It is not possible to
show data from a query directly; the database owner must then create a view
of the query, from which then a chart may be produced.

### Create your own chart

It is possible for an anonymous user to create a chart from a table or view.

- Go to the table rows page for
  [iris_flower_measurements](https://dbshare.scilifelab.se/table/demo/iris_flower_measurements). Click on **Chart**.
- The page shows the chart templates that are currently available.
- Click on **Basic two-dimensional scatterplot**.
- This shows a number of rows, where each rows is a mapping of the columns
  in the table to the available plot dimensions. In this case, there are
  only two numerical dimensions, so all permutations of the four numerical
  columns are shown.
- Click on **Render** for any of the mappings. This will show the chart.
- An anonymous user can't easily make any tweaks to the chart. 
  It's basically take it or leave it.
- A logged-in user can save the chart and then edit the Vega-Lite code
  in any way, assuming knowledge of Vega-Lite.
- It is possible to save the chart as a PNG or SVG file by clicking the
  symbol **...** in the upper right corner of the chart.
- It is also possible to view the
  [Vega-Lite](https://vega.github.io/vega-lite/) JSON code for the chart,
  which can be used by a Vega-Lite expert to download, edit, 
  or use as a template for other purposes.
