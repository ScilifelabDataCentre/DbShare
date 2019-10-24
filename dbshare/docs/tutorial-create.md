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
- A maximum of ten columns can be defined in this interface.
    - Provide the column name.
    - Choose which data type the column should have.
    - Decide if the column should be a primary key. Only one column
      can be set as primary key in this interface.
    - Decided if the column should be "NOT NULL", i.e. require a value.

### Create a view

- A view can be useful when a subset of the data is to be presented, while
  ensuring that any updates in the source tables is automatically manifested
  in the view.
