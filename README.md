# Pleko

Explore, visualize and publish data sets with
[Sqlite3](https://www.sqlite.org/) and 
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
- Download the Sqlite3 file containing a database.
- Upload a database Sqlite3 file.

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
- Update rows in a table by uploading a CSV file. *TODO*
- Clone a table.
- Delete a table.
- Download a table as CSV file.
- Fetch data in CSV or JSON format.
- List the visualizations based on a table.
- Add a column to a table. *TODO*
- Define a foreign key. *TODO*

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
  [Vega-Lite](https://vega.github.io/vega-lite/).
- Display a visualization.
- Clone a visualization.
- Edit a visualization.

## API (JSON)

*TODO*

## Access privileges

*TODO*

## Third-party packages used

- [Flask](http://flask.pocoo.org/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Jinja2](http://jinja.pocoo.org/)
- [jsonschema](https://github.com/Julian/jsonschema)
- [dpath-python](https://github.com/akesterson/dpath-python)
