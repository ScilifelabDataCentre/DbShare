# Pleko

Explore, visualize and publish data sets with
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
- Databases are isolated from one another.
- Display the tables, views, indexes and visualizations in a database.
- Download the Sqlite3 file containing a database.
- Upload a database Sqlite3 file.

## Tables

- Create a table, defining the columns.
- Insert a row of data.
- Edit a row.
- Delete a row.
- Display the rows in a table.
- Display the schema of a table.
- List the visualizations of a table.
- Insert rows in a table by uploading a CSV file.
- Update rows in a table by uploading a CSV file. *TODO*
- Create a table by uploading a CSV file.
- Clone a table.
- Delete a table.
- Download a table as CSV file.
- Fetch data in CSV or JSON format.
- Add a column to a table. *TODO*
- Define a foreign key. *TODO*

## Queries

- Query the tables in a database.
- A query is specified using Sqlite3 SQL.
- Queries are made towards the database in read-only mode, hence are secure.
- Edit the query.
- Make a view out of the query.

## Views

- Create a view.
- Display the rows of a view.
- Display the schema of a view.
- List the visualizations of a view.
- Delete a view.
- Clone a view.
- Download a view as CSV file.
- Fetch data in CSV or JSON format.

## Indexes

- Create an index.
- View the schema of an index.
- Delete an index.

## Visualization

- Create a visualization of a table or view using
  [Vega-Lite](https://vega.github.io/vega-lite/).
- Display a visualization.
- Clone a visualization.
- Edit a visualization.

## API (JSON)

*TODO*

## Access privileges

*TODO*

## URLs

- **/** Home page; list of public databases.
- **/upload** Upload a Pleko Sqlite3 database file.
- **/all** List of all databases (admin only).
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
   Delete the table.
- **/table/{dbname}/{tablename}/schema** Display the schema of the table.
- **/table/{dbname}/{tablename}/row** Insert a row into the table.
- **/table/{dbname}/{tablename}/insert** Insert data from a file into the table.
- **/table/{dbname}/{tablename}/update** Update the table from data i a file.
- **/table/{dbname}/{tablename}/clone** Clone the table.
- **/table/{dbname}/{tablename}/download** Download the rows in the table
  to a file.
- **/view/{dbname}** Create a view of the data in the database.
- **/view/{dbname}/{viewname}** Display the rows of the view. Delete the view.
- **/view/{dbname}/{viewname}/schema** Display the definition of the view.
- **/view/{dbname}/{viewname}/clone** Clone the view.
- **/view/{dbname}/{viewname}/download** Download the rows in the view
  to a file.
- **/vega-lite** Create a Vega-Lite visualization.
- **/visual/{dbname}** List the visualizations in the database.
- **/visual/{dbname}{visualname}** Display the visualization.
  Delete the visualization
- **/visual/{dbname}/{visualname}/edit** Edit the visualization.
- **/visual/{dbname}/{visualname}/clone** Clone the visualization.

## Third-party packages used

- [Flask](http://flask.pocoo.org/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Jinja2](http://jinja.pocoo.org/)
- [jsonschema](https://github.com/Julian/jsonschema)
- [dpath-python](https://github.com/akesterson/dpath-python)
