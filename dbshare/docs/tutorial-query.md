# Tutorial: Query and view

Query the contents of a database using SQL. A view is a saved query.

### Query

- The query page can be reached from the database page, or from the table
  rows page.
- The different parts of a SELECT query are shown. Only the `**SELECT**`
  and the `**FROM**` parts are strictly required.
- The LIMIT part is set by default to 200 result rows. This may be deleted
  or modified. However, not more than 2,000 rows will be returned from
  the server, for performance reasons.
- There is a limit to the execution (CPU) time allowed for a query.
  A query will be aborted if it exceeds this limit.
- Currently, there is no way to query data from more than one database.

### View

- A view in SQL-speak is a saved query. It looks like a table, but
  there is no separate table.
- A view is nothing magical; each time it is accessed,
  its saved query is re-run.
- A view can be useful when a subset of the data is to be presented, while
  ensuring that any updates in the tables used in the query are automatically
  manifested in the view.
- If a view is used often on data that is not changed, or changed very
  rarely, then it is likely more efficient to create a new table from the view,
  and use this table.

