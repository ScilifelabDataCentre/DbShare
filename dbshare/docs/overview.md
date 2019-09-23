The DbShare system allows web access to data published in the form of
[SQLite3](https://www.sqlite.org/) relational databases. Queries on
the data can be performed using SQL.

The data may be visualized in charts based on predefined stencils
(templates) using the [Vega-Lite](https://vega.github.io/vega-lite/)
specification format.

### Databases

A database contains tables and optionally, indexes views and charts. A
database is a single SQLite3 file. The web interface of DbShare allows
displaying and querying the data in a database using SQL. The metadata
of the database (schema, indexes, etc) can be viewed. A DbShare
instance may host many databases. A database is completely isolated
from other databases. Its name is unique in each DbShare instance.

### Web and API interfaces

There are two interfaces to the system: The web HTML-based interface
for humans, and the JSON-based API for programmatic access via scripts
executing on e.g. the user's computer. Other web sites may link
to the data or charts of a DbShare instance, if the access privileges
allow it.

#### Creation

Only users with an account may create databases in the site. A
database may be created from scratch, and its tables, indexes, views
and charts to be defined via the web interface.  An existing SQLite3
file may be uploaded. The system will inspect the data in it and and
attempt to infer the DbShare-related metadata from it.

#### Ownership

A database is owned by the user account that created it. Only the
owner can edit or delete the database and edit its contents. An
account has a quota for the total size of the databases owned by it.

#### Private and public access

A database is by default private, in which case only the owner of it
can access it. The database owner may set the database to being
public, which means that anyone, including anonymous users, can access
and query the data.

#### Read/write or read-only

A database is read/write by default. The owner of a database may set
it to be read-only, thus ensuring that no modifying operations can be
performed on it.

#### Database operations

Only the owner of a database may edit, add or delete data in it.  A
database may be cloned, creating a complete copy of it.  A database
may be renamed. This should not be done to public database, since its
URL will change, potentially invalidating external links to it.  Only
the owner of a database may delete it.

#### Download

A SQLite3 database file can be downloaded. Tables, views and queries
can be downloaded as CSV or JSON format files.

### Tables

A table is a relational table in an SQLite database. All data in a
database are stored in tables.  The owner of a database may create a
table in it, defining its columns, and load data into it in several
different way.

A table contains data in row/column form, with each data item being
either an integer, a real (float) or a text value. The schema of the
table defines the columns. A table can be created, or added to, by
uploading a CSV file. Single rows may also be added, edited or delete.

Simple statistics can be computed for the columns of the table. A
table may be cloned into a separate copy. The table's data may be
accessed from external systems as JSON or downloaded as a CSV file.

### Views

A view is a stored query that looks like a table; each access to it
actally performs the query on the database. One may create a table
from a view, thus creating a snapshot of the state of the table. The
view's data may be accessed from external systems as JSON or
downloaded as a CSV file.

### Queries

A query is simply an ordinary SQL query statement. Any user, including
an anonymous user (not logged in) may execute queries on public
data. A query may be saved as a view.

Queries are always performed in read-only mode, hence are
secure. There is a limit of the CPU time a query may use. A query can
involve only one database; currently, it is not possible to perform
cross-database queries.

### Indexes

Indexes are used to optimize queries involving the table of the
index. They can also be defined to disallow non-unique values in a
column.

### Charts

The data in a table or view may be visualized on a chart using the
[Vega-Lite](https://vega.github.io/vega-lite/) specification
format. There are a set of chart templates which can be used to
quickly create a chart which can be saved in the database. The charts
are dynamic in the sense that each time the chart is viewed, the data
is read from the database.  The Vega-Lite code of the saved charts may be
edited.
