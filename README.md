# Pleko

Web-based relational database system powered by Sqlite.

πλέκω: to plait, twine, twist, weave, braid

## `/`

List of databases, depending on access for logged-in user.

## `/db`

Create a database.

## `/db/{dbid}`

List of tables (with # rows).

List of views.

Delete the database.

## `/db/{dbid}/upload`

Upload a data file, creating a table in the database.

## `/table/{dbid}`

Create a table in the database.

## `/table/{dbid}/{tableid}`

Display rows from the table.

Delete the table.

## `/table/{dbid}/{tableid}/schema`

Display table definition.

Display its indexes.

## `/table/{dbid}/{tableid}/row`

Add a row to the table.

## `/table/{dbid}/{tableid}/column`

Add a column to the table.

## `/table/{dbid}/{tableid}/index`

Create an index in the table.

## `/table/{dbid}/{tableid}/index/{indexid}`

Delete the index.

## `/table/{dbid}/{tableid}/upload`

Upload a data file, adding rows to the table.

## `/query/{dbid}`

Perform a query.

## `/view/{dbid}`

Create a view.

## `/view/{dbid}/{vid}`

Display view rows.

Delete the view.
