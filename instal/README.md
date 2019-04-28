Installation
============

The DbPortal system is a Flask app which is typically served by some
third-party web server, such as gunicorn, or nginx via uwsgi.

This directory contains a few files that may be helpful in setting up
the service.

`dbportal.service`: a `systemd` file for starting the uwsgi server.

`uwsgi.ini`: an initialization file for the uwsgi server.
