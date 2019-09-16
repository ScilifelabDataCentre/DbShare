"Chart HTML endpoints."

import copy
import glob
import http.client
import json
import os.path

import flask
import jinja2
import jsonschema

import dbshare.db
import dbshare.schema.chart

from . import constants
from . import utils


blueprint = flask.Blueprint('chart', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
def save(dbname):
    "Save the chart in the database given the table/view and template."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        sourcename = flask.request.values['sourcename']
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        templatename = flask.request.values['templatename']
    except KeyError:
        utils.flash_error('no such template')
        return flask.redirect(flask.url_for('.select',
                                            dbname=dbname,
                                            sourcename=sourcename))
    try:
        template = get_template(templatename)
        context = get_context(db, schema, template)
        spec = get_chart_spec(template, context)
    except (KeyError, ValueError) as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for('.select',
                                            dbname=dbname,
                                            sourcename=sourcename))

    if utils.http_GET():
        return flask.render_template('chart/save.html',
                                     db=db,
                                     schema=schema,
                                     templatename=templatename,
                                     context=context)

    elif utils.http_POST():
        try:
            with dbshare.db.DbContext(db) as ctx:
                chartname = flask.request.form['name']
                ctx.add_chart(chartname, schema, spec)
        except (ValueError, jsonschema.ValidationError) as error:
            utils.flash_error(str(error))
            return flask.redirect(flask.url_for('.select',
                                                dbname=dbname,
                                                sourcename=sourcename))
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))

@blueprint.route('/<name:dbname>/<nameext:chartname>')
def display(dbname, chartname):
    "Display the saved database chart."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        chart = db['charts'][str(chartname)]
    except KeyError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))
    try:
        schema = dbshare.db.get_schema(db, chart['source'])
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if chartname.ext == 'json' or utils.accept_json():
        return flask.jsonify(chart['spec'])

    elif chartname.ext in (None, 'html'):
        url = flask.url_for('.display', dbname=dbname, chartname=chartname)
        return flask.render_template('chart/display.html',
                                     db=db,
                                     schema=schema,
                                     chart=chart,
                                     has_write_access=dbshare.db.has_write_access(db),
                                     json_url=url + '.json')

@blueprint.route('/<name:dbname>/<name:chartname>/edit',
                 methods=['GET', 'POST', 'DELETE'])
def edit(dbname, chartname):
    "Edit the named chart. Or delete it."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))
    try:
        chart = db['charts'][str(chartname)]
    except KeyError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))

    if utils.http_GET():
        return flask.render_template('chart/edit.html', db=db, chart=chart)

    elif utils.http_POST():
        try:
            spec = json.loads(flask.request.form['spec'])
            with dbshare.db.DbContext(db) as ctx:
                ctx.update_chart(chartname, spec)
        except (KeyError, ValueError, jsonschema.ValidationError) as error:
            utils.flash_error(error)
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))

    elif utils.http_DELETE():
        with dbshare.db.DbContext(db) as ctx:
            ctx.delete_chart(chartname)
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:sourcename>/select')
def select(dbname, sourcename):
    "Display selection of templates to make a chart for the given table/view."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    templates = get_templates()
    for template in templates:
        template['combinations'] = combinations(template['variables'], schema)
    templates = [t for t in templates if t['combinations']]
    return flask.render_template('chart/select.html',
                                 db=db,
                                 schema=schema,
                                 templates=templates)

def combinations(variables, schema, current=None):
    "Return all combinations of variables in template to table/view columns."
    result = []
    if current is None:
        current = []
    pos = len(current)
    for column in schema['columns']:
        # if annotations.get(column['name'], {}).get('ignore'): continue
        if isinstance(variables[pos]['type'], str):
            if column['type'] != variables[pos]['type']: continue
        elif isinstance(variables[pos]['type'], list):
            if column['type'] not in variables[pos]['type']: continue
        else:
            continue
        # XXX check annotation in variable, when implemented
        if column['name'] in current: continue
        if pos + 1 == len(variables):
            result.append(dict(zip([v['name'] for v in variables],
                                   current + [column['name']])))
        else:
            result.extend(combinations(variables,
                                       schema,
                                       current+[column['name']]))
    return result

@blueprint.route('/<name:dbname>/<name:sourcename>/<nameext:templatename>')
def render(dbname, sourcename, templatename):
    "Render the chart for the given table/view and template."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        template = get_template(str(templatename))
        context = get_context(db, schema, template)
        spec = get_chart_spec(template, context)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.select', dbname=dbname, sourcename=sourcename))

    if templatename.ext == 'json' or utils.accept_json():
        return utils.jsonify(spec)

    elif templatename.ext in (None, 'html'):
        json_url = utils.url_for('.render',
                                 dbname=db['name'],
                                 sourcename=schema['name'],
                                 templatename=template['name'] + '.json',
                                 _query=context)
        return flask.render_template('chart/render.html',
                                     title=context['title'],
                                     db=db,
                                     has_write_access=dbshare.db.has_write_access(db),
                                     schema=schema,
                                     templatename=template['name'],
                                     spec=spec,
                                     context=context,
                                     json_url=json_url)

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)

def get_context(db, schema, template):
    """Return the context for producing a chart from the template.
    Get values from the request.
    Raise ValueError if anything is wrong.
    """
    try:
        result = {
            'url': utils.url_for_rows(db, schema, external=True, csv=True),
            'title': flask.request.values.get('title') or
                     f"{schema['type'].capitalize()} {schema['name']}: {template['name']}",
            'width': int(flask.request.values.get('width') or
                         flask.current_app.config['CHART_DEFAULT_WIDTH']),
            'height': int(flask.request.values.get('height') or
                         flask.current_app.config['CHART_DEFAULT_HEIGHT'])
        }
    except TypeError as error:
        raise ValueError(str(error))
    for variable in template['variables']:
        colname = flask.request.values.get(variable['name'])
        if not colname: 
            raise ValueError(f"no column for variable {variable['name']}")
        for column in schema['columns']:
            if column['name'] == colname: break
        else:
            raise ValueError(f"no such column {colname}")
        result[variable['name']] = colname
    return result

def get_chart_spec(template, context):
    """Return the chart spec given the template and the context.
    Raise ValueError if something is wrong.
    """
    try:
        result = jinja2.Template(template['template']).render(**context)
        result = json.loads(result)
        utils.json_validate(result,flask.current_app.config['VEGA_LITE_SCHEMA'])
    except (jinja2.TemplateError, jsonschema.ValidationError) as error:
        raise ValueError(str(error))
    return result

def get_templates():
    "Return the available templates."
    return copy.deepcopy(TEMPLATES)

def get_template(templatename):
    try:
        return copy.deepcopy(TEMPLATES_LOOKUP[templatename])
    except KeyError:
        raise ValueError('no such chart template')

TEMPLATES = []
TEMPLATES_LOOKUP = {}

def init(app):
    "Read the templates from file."
    filenames = glob.glob(f"{ app.config['CHART_TEMPLATES_DIRPATH'] }/*.json")
    for filename in filenames:
        load_template(filename)
    dirpath = app.config['SITE_CHART_TEMPLATES_DIRPATH']
    if dirpath:
        dirpath = os.path.expandvars(os.path.expanduser(dirpath))
        filenames = glob.glob(f"{ dirpath }/*.json")
        for filename in filenames:
            load_template(filename)
    TEMPLATES.sort(key=lambda s: s['name'])

def load_template(filename):
    "Load the template from the given file."
    with open(filename) as infile:
        template = json.load(infile)
    try:
        filename = filename.replace('.json', '.template')
        with open(filename) as infile:
            template['template'] = infile.read()
    except IOError: # The 'template' item may already have been defined
        pass        # in the JSON file.
    utils.json_validate(template, dbshare.schema.chart.template_schema)
    # Replace template in list if already loaded.
    if template['name'] in TEMPLATES_LOOKUP:
        for pos, st in enumerate(TEMPLATES):
            if st['name'] == template['name']:
                TEMPLATES[pos] = template
                break
    else:
        TEMPLATES.append(template)
    TEMPLATES_LOOKUP[template['name']] = template
