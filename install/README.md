Installation
============

The databases for DbShare will be located in the directory specified
by the settings variable `DATABASES_DIRPATH` which must contain the
absolute path of the directory. The directory must exist and allow
`read/write` for the HTTP server.

The DbShare system is a Flask app which is typically served by some
third-party web server, such as `nginx` (via `uwsgi`).

This directory contains a few files that may be helpful in setting up
the service.

`dbshare.conf`: an `nginx` configuration file for reverse-proxy of the
`uwsgi` server.

`dbshare.service`: a `systemd` file for starting the `uwsgi` server on
an SELinux system.

`uwsgi.ini`: an initialization file for the `uwsgi` server.

On SELinux one needs to allow socket communication if it is to be used
between nginx and uwsgi. If the socket is placed in the
`/var/www/apps/DbShare` directory, one may do:

```
# chcon -Rt httpd_sys_content_rw_t /var/www/apps/DbShare
```