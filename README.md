# DbPortal

Web service to share tabular data sets in
[Sqlite3](https://www.sqlite.org/) databases.
Visualize with
[Vega](https://vega.github.io/vega/) or
[Vega-Lite](https://vega.github.io/vega-lite/).

## Databases

- A database may contain tables, views, indexes and visualizations.
- A database is owned by the user account that created it.
- A database may be private or public.
- A database may be read/write or read-only.
- Databases are isolated from one another.
- Display the tables, views, indexes and visualizations in a database.
- Create a database.
- Rename a database.
- Clone a database.
- Delete a database.
- Download the Sqlite3 file containing one database and its DbPortal metadata.
- Upload a Sqlite3 database file (plain, or containing DbPortal metadata).

## Tables

- A table contains data in row/column form.
- The available data types are: integer, real, text.
- Create a table, defining the columns; i.e. schema.
- Create a table by uploading a CSV file.
- Display the rows in a table.
- Display the schema of a table.
- List the visualizations for a table.
- Insert a row of data.
- Edit a row.
- Delete a row.
- Insert rows in a table by uploading a CSV file.
- Update rows in a table by uploading a CSV file.
- Clone a table.
- Delete a table.
- Download a table as a CSV file.
- Fetch the rows of the table in CSV or JSON format.

## Queries

- Query the tables in a database.
- A query is written using the Sqlite3 SQL language.
- A query can involve only one database; cross-database queries are
  currently not possible.
- Queries are performed with the database in read-only mode, hence are secure.
- Edit the query and re-run it.
- Create a view out of the query.

## Views

- A view is a predefined query which can be used as if it were a table.
- Display the rows of a view.
- Display the definition of a view.
- List the visualizations for a view.
- Create a view from a query.
- Delete a view.
- Clone a view.
- Download the view data as a CSV file.
- Fetch the rows of the view in CSV or JSON format.

## Indexes

- Indexes optimize certain queries involving a given table.
- Indexes can be used to ensure that row values are unique in the table.
- Create an index.
- View the schema of an index.
- Delete an index.

## Visualization

- Create a visualization of a table or view using
  [Vega](https://vega.github.io/vega/) or
  [Vega-Lite](https://vega.github.io/vega-lite/).
- Display a visualization.
- Clone a visualization.
- Edit a visualization.
- Create a visualization template (Vega or Vega-Lite) with input fields
  for pre-packaged charts.

## Software used

- [Sqlite3](https://www.sqlite.org/)
- [Flask](http://flask.pocoo.org/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Jinja2](http://jinja.pocoo.org/docs)
- [Vega](https://vega.github.io/vega/)
- [Vega-Lite](https://vega.github.io/vega-lite/)
- [jsonschema](https://github.com/Julian/jsonschema)
- [dpath-python](https://github.com/akesterson/dpath-python)
- [Bootstrap](https://getbootstrap.com/)
- [jQuery](https://jquery.com/)
- [jQuery localtime](https://plugins.jquery.com/jquery.localtime/)
- [DataTables](https://datatables.net/)
