The DbShare system allows web access to data published in the form of
[SQLite3](https://www.sqlite.org/) relational databases. Queries on
the data can be performed using SQL.

The data may be visualized in charts based on predefined stencils
(templates) using the [Vega-Lite](https://vega.github.io/vega-lite/)
specification format.

There is a JSON-based API for programmatic access. Other web sites may
use or refer to data stored in a DbShare instance.

### Databases

A database contains tables and optionally, indexes views and charts. A
database is a single SQLite3 file.

The web interface of DbShare allows displaying and querying the data
in a database using SQL. The metadata of the database (schema,
indexes, etc) can be viewed.

A DbShare instance may host many databases. A database is completely
isolated from other databases. It is currently not possible to
performa queries across two or more databases simultaneously.

#### Creation

Only users with an account at a site may create databases there.

A database may be created from scratch, and its tables, indexes, views
and charts to be defined via the web interface.

An existing SQLite3 file may be uploaded. The system will inspect the
data in it and and attempt to infer the DbShare-related metadata from
it.

#### Ownership

A database is owned by the user account that created it. Only the
owner can edit or delete the database.

Data may be added, edited and deleted via the web interface.

#### Private and public access

A database is by default private, in which case only the owner of it can
access it.

The database owner may set the database to being public, which means
that anyone, including anonymous users, can access and query the data.

#### Read/write or read-only

A database is read/write by default. The owner of a database may set
it to be read-only, thus ensuring that no modifying operations can be
performed on it.

#### Database operations

Only the owner of a database may edit, add or delete data in it.

A database may be cloned, creating a complete copy of it.

A database may be renamed. This should not be done to public database,
since its URL will change, potentially invalidating external links to
it.

Only the owner of a database may delete it.

#### Download

A SQLite3 database file can be downloaded. Tables, views and queries
can be downloaded as CSV or JSON format files.

### Tables

A table is a relational table in an SQLite database. All data in a
database are stored in tables.

The owner of a database may create a table in it, defining its
columns, and load data into it in several different way.

### Views

A view is a stored query that looks like a table, but each access
to it actally performs the query on the database.
