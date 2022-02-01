"About HTML endpoints."

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

from . import constants
from . import utils


blueprint = flask.Blueprint('about', __name__)

@blueprint.route('/documentation/<page>')
def documentation(page):
    "Documentation page in Markdown format."
    filepath = os.path.join(flask.current_app.config['DOCUMENTATION_DIR'], f"{page}.md")
    try:
        with open(filepath) as infile:
            text = infile.read()
    except (OSError, IOError):
        flask.abort(http.client.NOT_FOUND)
    title = page.replace('-', ' ')
    return flask.render_template('about/documentation.html', title=title, text=text)

@blueprint.route('/contact')
def contact():
    "Display the contact information page."
    return flask.render_template('about/contact.html',
                                 text=utils.get_site_text("contact.md"))

@blueprint.route('/gdpr')
def gdpr():
    "Display the personal data policy page."
    return flask.render_template('about/gdpr.html',
                                 text=utils.get_site_text("gdpr.md"))

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
                                 schemas=dbshare.api.schema.get_schemas())

@blueprint.route('/software')
def software():
    "Display software in system with links and version info."
    config = flask.current_app.config
    v = sys.version_info
    software = [
        ('DbShare', dbshare.__version__, constants.URL),
        ('Python', f"{v.major}.{v.minor}.{v.micro}", 'https://www.python.org/'),
        ('Sqlite3', sqlite3.version, 'https://www.sqlite.org/'),
        ('Flask', flask.__version__, 'http://flask.pocoo.org/'),
        ('Flask-Mail', flask_mail.__version__, 'https://pythonhosted.org/Flask-Mail'),
        ('Jinja2', jinja2.__version__, 'http://jinja.pocoo.org/docs'),
        ('jsonschema', jsonschema.__version__, 'https://github.com/Julian/jsonschema'),
        ('dpath-python', constants.DPATH_VERSION, constants.DPATH_URL),
        ('Bootstrap', constants.BOOTSTRAP_VERSION, constants.BOOTSTRAP_URL),
        ('jQuery', constants.JQUERY_VERSION, constants.JQUERY_URL),
        ('jQuery.localtime', constants.JQUERY_LOCALTIME_VERSION, constants.JQUERY_LOCALTIME_URL),
        ('DataTables', constants.DATATABLES_VERSION, constants.DATATABLES_URL),
    ]
    return flask.render_template('about/software.html', software=software)

@blueprint.route('/settings')
@utils.admin_required
def settings():
    config = flask.current_app.config.copy()
    for key in ['SECRET_KEY', 'MAIL_PASSWORD']:
        if config.get(key):
            config[key] = '<hidden>'
    return flask.render_template('about/settings.html',
                                 items=sorted(config.items()))
