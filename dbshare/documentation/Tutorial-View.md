- An SQL view is a saved query. It looks like a table, but there is no
  separate table.
- A view is nothing magical; each time it is accessed, its saved query
  is re-run.
- A view can be useful when a subset of the data is to be presented,
  while ensuring that any updates in the tables used in the query are
  automatically manifested in the view.
- If a view is used often on data that is not changed, or changed very
  rarely, then it is likely more efficient to create a new table from
  the view, and use this table.

