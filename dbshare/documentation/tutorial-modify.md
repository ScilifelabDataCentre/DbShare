---
title: Modify table contents
ordinal: 103
---

If you have an account (see [Register a user account](/user/register)),
and have logged in (see [Login](/user/login)), you will be able to
modify your own databases.

### Add data to the table

- Go to the table rows page of the table (Click the button **0 rows**.)
- Click **Insert row**. This page allows adding a row of data.
- When **Insert** is clicked, the data is appended to the table.
  The same input page is shown again. This allows adding many rows after each
  other with minimum clicking.
- Click the button **N rows** (where N is the number of rows in the table".
  The current rows in the table are shown. The table is shown in chunks, 
  and it is possible to search for items in it. At most
  2,000 rows are fetched from the server, for performance reasons.
  The SQLite3 database itself can handle millions of rows in a table.

### Edit a row in the table

- By each row, there is an **Edit** button. Clicking this shows a page where
  the values in the row can be modified.
- It is also possible to delete the entire row.
