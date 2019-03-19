# Pleko

Web-based relational database system powered by Sqlite.

πλέκω: to plait, twine, twist, weave, braid

## `/`

List of databases, depending on access for logged-in user.

## `/db`

Create a database.

## `/db/{dbid}`

List of tables (with # rows).

List of views. TODO

Delete the database.

## `/table/{dbid}`

Create a table in the database.

## `/schema/{dbid}`

View tables (with # rows).

View indexes. TODO

## `/schema/{dbid}/{tableid}`

View table definition.

View indexes. TODO

Delete table.

## `/table/{dbid}/{tableid}`

Display rows from the table. TODO

## `/table/{dbid}/{tableid}/add`

Add a row to the table.

## `/column/{dbid}/{tableid}`

Add a column to the table. TODO

## `/index/{dbid}/{tableid}`

Create an index in the table. TODO

## `/index/{dbid}/{tableid}/{indexid}`

Delete the index. TODO

## `/query/{dbid}`

Perform a query. TODO

## `/view/{dbid}`

Create a view. TODO

## `/view/{dbid}/{vid}`

Display view rows. TODO

Delete view. TODO

## `/upload/{dbid}`

Upload a data file, creating a table. TODO

## `/upload/{dbid}/{tableid}`

Upload a data file, adding rows to the table. TODO

## `/download/{dbid}/{tableid}`

Download a data file from the table. TODO
