# Pleko

Web tool to explore, publish and plot data sets using
[Sqlite3](https://www.sqlite.org/) and 
[Vega-Lite](https://vega.github.io/vega-lite/).

πλέκω: to plait, twine, twist, weave, braid

## Databases

- Create a database to contain tables, views and indexes.
- Rename a database.
- Clone a database.
- Delete a database.
- A database is owned by the user account that created it.
- A database may be private or public.
- Databases are independent of one another.
- Display the tables, views and indexes in a database.
- Download the Sqlite3 table for a database.

## Tables

- Create a table, defining the columns.
- Insert a row.
- Edit a row.
- Delete a row.
- Display the rows in a table.
- Display the schema of a table.
- Upload CSV data to a table, inserting rows.
- Upload CSV data to a table, updating rows. *TODO*
- Create a table from a CSV file.
- Clone a table.
- Delete a table.
- Download a table as CSV file.
- Add a column to a table. *TODO*
- Define a foreign key. *TODO*

## Queries

- Query the tables in a database.
- Edit the query.
- Make a view out of the query.

## Views

- Create a view.
- Edit a view. *TODO*
- Display the rows of a view.
- Display the schema of a view.
- Delete a view.
- Clone a view.
- Download a view as CSV file.

## Indexes

- Create an index.
- View the schema of an index.
- Delete an index.

## Plots

- Select plot type and table/view.
- Create a plot.
- Display a plot.
- Clone a plot.
- Edit a plot.
- Create and edit a plot using explicit Vega-Lite spec.

## Access privileges

*TODO*

## API (JSON)

*TODO*

## URLs

- **/** Home page; list of public databases.
- **/upload** Upload a Pleko Sqlite3 database file.
- **/all** List all databases (admin only).
- **/owner/{username}** List all databases belonging the user.
- **/db** Create a database.
- **/db/{dbname}** Summary of database contents. Delete database.
- **/db/{dbname}/rename** Rename the database.
- **/db/{dbname}/logs** Display log of database changes.
- **/db/{dbname}/upload** Create a table from a CSV file.
- **/db/{dbname}/clone** Clone the database.
- **/db/{dbname}/download** Download the database Sqlite3 file.
- **/db/{dbname}/public** Set the database to public access.
- **/db/{dbname}/private** Set the database to private access.
- **/db/{dbname}/readwrite** Set the database to read-write mode.
- **/db/{dbname}/readonly** Set the database to read-only mode.
- **/table/{dbname}** Create a table in the database.
- **/table/{dbname}/{tablename}** Display the rows of the table.
- **/table/{dbname}/{tablename}/schema** Display the schema of the table.
- **/table/{dbname}/{tablename}/row** Insert a row into the table.
- **/table/{dbname}/{tablename}/upload** Insert data from a file into the table.
- **/table/{dbname}/{tablename}/clone** Clone the table.
- **/table/{dbname}/{tablename}/download** Download the rows in the table to a file.
- **/view/{dbname}** Create a view of the data in the database.
- **/view/{dbname}/{viewname}** Display the rows of the view.
- **/view/{dbname}/{viewname}/schema** Display the definition of the view.
- **/view/{dbname}/{viewname}/clone** Clone the view.
- **/view/{dbname}/{viewname}/download** Download the rows in the view to a file.
- **/plot/{dbname}** List the plots in the database.
- **/plot/{dbname}/display/{plotname}** Display the given plot in the database.
- **/plot/{dbname}/select** Select plot type and table/view.
- **/plot/{dbname}/create/{plottype}/{tableviewname}** Create the given plot.
- **/plot/{dbname}/edit/{plotname}** Edit the plot.
- **/plot/{dbname}/clone/{plotname}** Clone the plot.

## Third-party packages used

- [Flask](http://flask.pocoo.org/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Jinja2](http://jinja.pocoo.org/)
- [jsonschema](https://github.com/Julian/jsonschema)
- [dpath-python](https://github.com/akesterson/dpath-python)
