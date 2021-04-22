The scripts in this directory are tests of the web API, using the
standard Python module `unittest`. The scripts interact with the
DbShare server using HTTP.

This is therefore a useful resource for examples of how to use the web
API.

Most of the scripts check the validity of the JSON responses using
schema in the local distribution. If you tests a remote DbShare server
that is running another version of the software compared to your local
copy of the code, some tests may fail.
