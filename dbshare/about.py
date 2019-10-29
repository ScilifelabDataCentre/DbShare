"About endpoints."

import os.path
import sqlite3
import sys

import flask
import flask_mail
import http.client
import jinja2
import jsonschema

import dbshare
import dbshare.api.schema
from dbshare import constants


blueprint = flask.Blueprint('about', __name__)

@blueprint.route('/doc/<pagename>')
def doc(pagename):
    "Documentation page in Markdown format."
    filepath = os.path.join(flask.current_app.config['DOCS_DIRPATH'],
                            pagename + '.md')
    try:
        with open(filepath) as infile:
            body = infile.read()
    except IOError:
        flask.abort(http.client.NOT_FOUND)
    if body.startswith('#'):
        title, body = body.split('\n', 1)
        title = title.lstrip('#').strip()
        body = body.strip()
    else:
        title = pagename.replace('-', ' ').capitalize()
    return flask.render_template('about/doc.html', title=title, body=body)

@blueprint.route('/endpoints')
def endpoints():
    "Display all URL endpoints."
    endpoints = {}
    trivial_methods = set(['HEAD', 'OPTIONS'])
    for rule in flask.current_app.url_map.iter_rules():
        endpoints[rule.endpoint] = {
            'url': rule.rule,
            'methods': sorted(rule.methods.difference(trivial_methods))}
    for name, func in flask.current_app.view_functions.items():
        endpoints[name]['doc'] = func.__doc__
    endpoints['static']['doc'] = 'Static web page support files.'
    urls = sorted([(e['url'], e) for e in endpoints.values()])
    return flask.render_template('about/url_endpoints.html', urls=urls)

@blueprint.route('/schema')
def schema():
    "Page with links to all JSON schema for the API."
    return flask.render_template('about/schema.html',
                                 schemas=dbshare.api.schema.schemas)

@blueprint.route('/software')
def software():
    "Display software in system with links and version info."
    config = flask.current_app.config
    v = sys.version_info
    data = [('DbShare',
             'https://github.com/pekrau/DbShare', dbshare.__version__),
            ('Python', 'https://www.python.org/',
             f"{v.major}.{v.minor}.{v.micro}"),
            ('Sqlite3', 'https://www.sqlite.org/', sqlite3.version),
            ('Flask', 'http://flask.pocoo.org/', flask.__version__),
            ('Flask-Mail',
             'https://pythonhosted.org/Flask-Mail', flask_mail.__version__),
            ('Jinja2', 'http://jinja.pocoo.org/docs', jinja2.__version__),
            ('Vega', 'https://vega.github.io/vega/', constants.VEGA_VERSION),
            ('Vega-Lite', 
             'https://vega.github.io/vega-lite/', constants.VEGA_LITE_VERSION),
            ('jsonschema', 
             'https://github.com/Julian/jsonschema', jsonschema.__version__),
            ('dpath-python',
             'https://github.com/akesterson/dpath-python', 
             constants.DPATH_VERSION),
            ('Bootstrap',
             'https://getbootstrap.com/', constants.BOOTSTRAP_VERSION),
            ('jQuery', 'https://jquery.com/', constants.JQUERY_VERSION),
            ('jQuery localtime', 
             'https://plugins.jquery.com/jquery.localtime/',
             constants.JQUERY_LOCALTIME_VERSION),
            ('DataTables', 
             'https://datatables.net/', constants.DATATABLES_VERSION),
    ]
    return flask.render_template('about/software.html', data=data)
