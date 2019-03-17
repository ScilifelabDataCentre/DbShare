# Pleko

Web-based relational database system, based on Sqlite.

πλέκω: to plait, twine, twist, weave, braid

## `/`

List of databases, depending on access for logged-in user.

## `/db`

Create a new database.

## `/db/{dbid}`

List of tables (# rows), views.

## `/db/{dbid}/table`

Create table.

## `/db/{dbid}/query`

Query multiple tables.

## `/db/{dbid}/view`

Create view.

## `/db/{dbid}/view/{vid}`

Display view rows.
Delete view.

## `/db/{dbid}/upload`

Upload CSV file, creating table.

## `/db/{dbid}/table/{tid}`

View table definition, indexes, etc.
Delete table.

## `/db/{dbid}/table/{tid}/column`

Create column.

## `/db/{dbid}/table/{tid}/index`

Create index.

## `/db/{dbid}/table/{tid}/index/{iid}`

Delete index.

## `/db/{dbid}/table/{tid}/rows`

Display table rows.

## `/db/{dbid}/table/{tid}/query`

Query the table.

## `/db/{dbid}/table/{tid}/upload`

Load CSV file.

## `/db/{dbid}/table/{tid}/download`

Download CSV file.

