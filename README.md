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

## `/table/{dbid}`

Create a table in the database.

## `/schema/{dbid}`

Display tables (with # rows).

## `/schema/{dbid}/{tableid}`

Display table definition.

Display indexes.

## `/table/{dbid}/{tableid}`

Display rows from the table.

Delete table.

## `/table/{dbid}/{tableid}/add`

Add a row to the table.

## `/column/{dbid}/{tableid}`

Add a column to the table.

## `/index/{dbid}/{tableid}`

Create an index in the table.

## `/index/{dbid}/{tableid}/{indexid}`

Delete an index.

## `/query/{dbid}`

Perform a query.

## `/view/{dbid}`

Create a view.

## `/view/{dbid}/{vid}`

Display view rows.

Delete view.

## `/upload/{dbid}`

Upload a data file, creating a table.

## `/upload/{dbid}/{tableid}`

Upload a data file, adding rows to the table.
