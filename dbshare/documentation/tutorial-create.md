---
title: Create databases and tables
level: 1
ordinal: 30
---

If you have an account (see [register](/user/register)), and have logged in
(see [login](/user/login)), you will be able to create your own databases.

### Create a database

- Go to the page showing [your databases](/dbs/owner)
  ("My databases" in the top menu.)
- Click **Create**.
- Provide a name for the database to create. The rules for a name are given
  in the help text.
- The title and descriptions are optional, but obviously useful for
  describing what the data is about.
- Clicking **Create** will create the database and bring you to its page.

### Upload a database

- Go to the page showing [your databases](/dbs/owner) ("My databases"
  in the top menu.)
- Click **Upload**.
- Select the file to upload from your local computer, and optionally
  specify a new name for the database.
- Clicking **Upload SQLite3 file** will upload it and the server will
  interpret the contents to extract the schema of the tables.
- It is also possible to upload an XLSX file (Excel). The server will
  try to interpret the contents as best as it can, and create a table
  for each worksheet.

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

### Upload a CSV file to create a table

- A table can also be created by uploading a CSV (Comma-Separated
  Values) file.  Such files can either by created "by hand", or by
  exporting a spreadsheet from Excel.
- In the database page, click **Upload table**.
- The page has input fields for the file itself, and for some details
  about the file layout. It is recommended to ensure that the CSV file
  contains a header record. If it exists, it must contain the names of
  the columns.
- The upload process infers the schema for the table from the contents
  of the CSV file.
