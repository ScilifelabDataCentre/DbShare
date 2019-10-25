# Tutorial: Create and modify a database

If you have an account (see [register](/user/register)), and have logged in
(see [login](/user/login)), you will be able to create your own databases.

### Create a database

- Go to the page showing [your databases](/dbs/owner)
  ("My databases" in the top menu."
- Click **Create**.
- Provide a name for the database to create. The rules for a name are given
  in the help text.
- The title and descriptions are optional, but obviously useful for
  describing what the data is about.
- Clicking **Create** will create the database and bring you to its page.

### The database page
- The database page is initially empty since no tables of views have been
  created.
- The buttons on the right show which operations are available. Some of the
  buttons display brief explanatory messages when hovering the mouse over them.
- Above the buttons are different download options.
- Below the buttons is some meta-information about the database.

### Create a table

- On the database page, click **Create table**.
- Provide a name for the table.
- A maximum of 8 columns can be defined in this interface.
    - Provide the column name.
    - Choose which data type the column should have.
    - Decide if the column should be a primary key. Only one column
      can be set as primary key in this interface.
    - Decided if the column should be "NOT NULL", i.e. require a value.
- Click **Create**. The table is created and its rows page is shown.
- Click **Schema** to verify that the table definition is what you expect.
- On this page, the buttons **Add column** and **Create index** can be used.

### Add data to the table

- Go to the table rows page of the table (Click the button **0 rows**.)
- Click **Insert row**. This page allows adding a row of data.
- When **Insert** is clicked, the data is appended to the table.
  The same input page is shown again. This allows adding many rows after each
  other with minimum clicking.
- Click the button **N rows** (where N is the number of rows in the table".
  The current rows in the table are shown. The table is shown in chunks, 
  and it is possible to search for items in it. At most
  2,000 rows are fetched from the server, for performance reasons.
  The SQLite3 database itself can handle millions of rows in a table.

### Edit a row in the table

- By each row, there is an **Edit** button. Clicking this shows a page where
  the values in the row can be modified.
- It is also possible to delete the entire row.

### Create a table from CSV upload

- A table can also be created by uploading a CSV (Comma-Separated Values) file.
  Such files can either by created "by hand", or by exporting a spreadsheet
  from Excel.
- In the database page, click **Upload table**.
- The page has input fields for the file itself, and for some details
  about the file layout. It is recommended to ensure that the CSV file
  contains a header record, i.e. the first line in it should contain the
  names of the columns.
- The upload process infers the schema for the table from the contents
  of the CSV file.

## Download a table

- A table can be downloaded as a CSV file. Use the **Download** button.
  The page allows some minor customization of the CSV file.
- Alternatively, the CSV data can be obtained directly using the
  pill (small rounded button) at the top right labelled **CSV**.
- Use the **JSON** pill to obtain that format.
- The two latter access methods are used by the visualization tool
  in DbShare which prepares charts based on Vega-Lite.

### Download a database

- There are several database download options.
- Clicking **Download** on the database page fetches the database as its
  native SQLite3 file.
- The pill labeled **CSV tar.gz' produces a gzipped tar archive file containing
  the CSV files for each of the tables in the database.
- The pill labeled **XLSX** creates an Excel file with each table in its
  separate worksheet.
