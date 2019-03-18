# Pleko

Web-based relational database system powered by Sqlite.

πλέκω: to plait, twine, twist, weave, braid

## `/`

List of databases, depending on access for logged-in user.

## `/db`

Create a database.

## `/db/{dbid}`

List of tables (# rows), views.
Delete the database.

## `/table/{dbid}`

Create a table in the database.

## `/column/{dbid}/{tid}`

Create a column in the table.

## `/index/{dbid}/{tid}`

Create an index in the table.

## `/index/{dbid}/{tid}/{iid}`

Delete the index.

## `/schema/{dbid}`

View all table definitions, indexes, etc.

## `/schema/{dbid}/{tid}`

View table definition, indexes, etc.
Delete table.

## `/row/{dbid}/{tid}`

Create a row in the table.

## `/rows/{dbid}/{tid}`

Display rows from the table.

## `/query/{dbid}`

Perform a query.

## `/view/{dbid}`

Create a view.

## `/view/{dbid}/{vid}`

Display view rows.
Delete view.

## `/upload/{dbid}`

Upload a data file, creating a table.

## `/upload/{dbid}/{tid}`

Upload a data file, adding rows to the table.

## `/download/{dbid}/{tid}`

Download a data file from the table.
