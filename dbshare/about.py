"About endpoints."

import sqlite3
import sys

import flask
import flask_mail
import jinja2
import jsonschema

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
        # print(rule.rule, rule.methods, rule.endpoint)
    for name, func in flask.current_app.view_functions.items():
        endpoints[name]['doc'] = func.__doc__
    endpoints['static']['doc'] = 'Static web page support files.'
    urls = sorted([(e['url'], e) for e in endpoints.values()])
    return flask.render_template('about/url_endpoints.html', urls=urls)

@blueprint.route('/software')
def software():
    "Display software in system with links and version info."
    config = flask.current_app.config
    v = sys.version_info
    data = [('DbShare', config['DBSHARE_URL'], config['VERSION']),
            ('Python', 'https://www.python.org/',
             f"{v.major}.{v.minor}.{v.micro}"),
            ('Sqlite3', config['SQLITE3_URL'], sqlite3.version),
            ('Flask', config['FLASK_URL'], flask.__version__),
            ('Flask-Mail',
             'https://pythonhosted.org/Flask-Mail', flask_mail.__version__),
            ('Jinja2', config['JINJA2_URL'], jinja2.__version__),
            ('Vega', config['VEGA_SITE_URL'], config['VEGA_VERSION']),
            ('Vega-Lite', 
             config['VEGA_LITE_SITE_URL'], config['VEGA_LITE_VERSION']),
            ('jsonschema', 
             'https://github.com/Julian/jsonschema', jsonschema.__version__),
            ('dpath-python',
             'https://github.com/akesterson/dpath-python', '1.4.2'),
            ('Bootstrap',
             config['BOOTSTRAP_SITE_URL'], config['BOOTSTRAP_VERSION']),
            ('jQuery', 
             config['JQUERY_SITE_URL'], config['JQUERY_VERSION']),
            ('jQuery localtime', 
             'https://plugins.jquery.com/jquery.localtime/', '0.9.1'),
            ('DataTables', 
             config['DATATABLES_SITE_URL'], config['DATATABLES_VERSION']),
    ]
    return flask.render_template('about/software.html', data=data)
