"About endpoints."

import sqlite3
import sys

import flask
import flask_mail
import jinja2
import jsonschema

import dbshare.api.schema

blueprint = flask.Blueprint('about', __name__)

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
    data = [('DbShare', 'https://github.com/pekrau/DbShare', config['VERSION']),
            ('Python', 'https://www.python.org/',
             f"{v.major}.{v.minor}.{v.micro}"),
            ('Sqlite3', 'https://www.sqlite.org/', sqlite3.version),
            ('Flask', 'http://flask.pocoo.org/', flask.__version__),
            ('Flask-Mail',
             'https://pythonhosted.org/Flask-Mail', flask_mail.__version__),
            ('Jinja2', 'http://jinja.pocoo.org/docs', jinja2.__version__),
            ('Vega', 'https://vega.github.io/vega/', config['VEGA_VERSION']),
            ('Vega-Lite', 
             'https://vega.github.io/vega-lite/', config['VEGA_LITE_VERSION']),
            ('jsonschema', 
             'https://github.com/Julian/jsonschema', jsonschema.__version__),
            ('dpath-python',
             'https://github.com/akesterson/dpath-python', '1.4.2'),
            ('Bootstrap',
             'https://getbootstrap.com/', config['BOOTSTRAP_VERSION']),
            ('jQuery', 'https://jquery.com/', config['JQUERY_VERSION']),
            ('jQuery localtime', 
             'https://plugins.jquery.com/jquery.localtime/', '0.9.1'),
            ('DataTables', 
             'https://datatables.net/', config['DATATABLES_VERSION']),
    ]
    return flask.render_template('about/software.html', data=data)
