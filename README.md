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

Delete the database. TODO

## `/table/{dbid}`

Create a table in the database.

## `/column/{dbid}/{tid}`

Create a column in the table. TODO

## `/index/{dbid}/{tid}`

Create an index in the table. TODO

## `/index/{dbid}/{tid}/{iid}`

Delete the index. TODO

## `/schema/{dbid}`

View tables (with # rows).

View indexes. TODO

## `/schema/{dbid}/{tid}`

View table definition.

View indexes. TODO

Delete table. TODO

## `/row/{dbid}/{tid}`

Create a row in the table. TODO

## `/rows/{dbid}/{tid}`

Display rows from the table. TODO

## `/query/{dbid}`

Perform a query. TODO

## `/view/{dbid}`

Create a view. TODO

## `/view/{dbid}/{vid}`

Display view rows. TODO

Delete view. TODO

## `/upload/{dbid}`

Upload a data file, creating a table. TODO

## `/upload/{dbid}/{tid}`

Upload a data file, adding rows to the table. TODO

## `/download/{dbid}/{tid}`

Download a data file from the table. TODO
