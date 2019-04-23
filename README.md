# Pleko

Upload, publish and query tabular data sets in
[Sqlite3](https://www.sqlite.org/) databases
and visualize with
[Vega](https://vega.github.io/vega/) or
[Vega-Lite](https://vega.github.io/vega-lite/).

πλέκω: to plait, twine, twist, weave, braid

## Databases

- A database may contain tables, views, indexes and visualizations.
- A database is owned by the user account that created it.
- A database may be private or public.
- Databases are isolated from one another.
- Display the tables, views, indexes and visualizations in a database.
- Create a database.
- Rename a database.
- Clone a database.
- Delete a database.
- Download the Sqlite3 file containing one database.
- Upload a Sqlite3 database file.

## Tables

- A table contains data in row/column form.
- The available data types are: integer, real, text.
- Create a table, defining the columns; i.e. schema.
- Create a table by uploading a CSV file.
- Display the rows in a table.
- Display the schema of a table.
- Insert a row of data.
- Edit a row.
- Delete a row.
- Insert rows in a table by uploading a CSV file.
- Update rows in a table by uploading a CSV file.
- Clone a table.
- Delete a table.
- Download a table as CSV file.
- Fetch data in CSV or JSON format.
- List the visualizations based on a table.

## Queries

- Query the tables in a database.
- A query can involve only one database; cross-database queries are
  currently not possible.
- A query is written in Sqlite3 SQL.
- Queries are made towards the database in read-only mode, hence are secure.
- Edit the query.
- Make a view out of the query.

## Views

- A view is a predefined query which can be used like a table.
- Display the rows of a view.
- Display the schema of a view.
- List the visualizations based on a view.
- Create a view from a query.
- Delete a view.
- Clone a view.
- Download a view as CSV file.
- Fetch data in CSV or JSON format.

## Indexes

- Indexes optimize certain queries of a given table.
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
