"Template HTMl endpoints."

import copy
import json

import flask
import jinja2
import jsonschema
import sqlite3

import dbportal.db
import dbportal.system
import dbportal.user
import dbportal.vega
import dbportal.vega_lite
from dbportal import constants
from dbportal import utils


blueprint = flask.Blueprint('template', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@dbportal.user.login_required
def create():
    "Create a template."
    if utils.http_GET():
        return flask.render_template('template/create.html')

    elif utils.http_POST():
        try:
            with TemplateContext() as ctx:
                ctx.set_name(flask.request.form.get('name'))
                ctx.set_title(flask.request.form.get('title'))
                ctx.set_type(flask.request.form.get('type'))
                if ctx.template['type'] == constants.VEGA:
                    initial = copy.deepcopy(dbportal.vega.INITIAL)
                    config = flask.current_app.config
                    initial['$schema'] = config['VEGA_SCHEMA_URL']
                    initial['width']   = config['VEGA_DEFAULT_WIDTH']
                    initial['height']  = config['VEGA_DEFAULT_HEIGHT']
                    ctx.set_code(json.dumps(initial, indent=2))
                elif ctx.template['type'] == constants.VEGA_LITE:
                    initial = copy.deepcopy(dbportal.vega_lite.INITIAL)
                    config = flask.current_app.config
                    initial['$schema'] = config['VEGA_LITE_SCHEMA_URL']
                    initial['width']   = config['VEGA_LITE_DEFAULT_WIDTH']
                    initial['height']  = config['VEGA_LITE_DEFAULT_HEIGHT']
                    ctx.set_code(json.dumps(initial, indent=2))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create'))
        return flask.redirect(
            flask.url_for('.display', templatename=ctx.template['name']))

@blueprint.route('/<name:templatename>')
def display(templatename):
    "Display the template definition."
    try:
        template = get_check_read(str(templatename))
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))
    write_access = has_write_access(template)
    fields = list(template['fields'].values())
    fields.sort(key=lambda f: f['ordinal'])
    return flask.render_template('template/display.html',
                                 template=template,
                                 fields=fields,
                                 has_write_access=write_access)

@blueprint.route('/<name:templatename>/download')
def download(templatename):
    "Download the template definition as a JSON file."
    try:
        template = get_check_read(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))
    data = {'$id': flask.request.url}
    data.update(template)
    response = flask.make_response(json.dumps(data))
    response.headers.set('Content-Type', constants.JSON_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename=template['name'] + '.json')
    return response

@blueprint.route('/<name:templatename>/edit', methods=['GET', 'POST', 'DELETE'])
@dbportal.user.login_required
def edit(templatename):
    "Edit the template definition. Or delete it."
    try:
        template = get_check_write(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))

    if utils.http_GET():
        return flask.render_template('template/edit.html', template=template)

    elif utils.http_POST():
        with TemplateContext(template=template) as ctx:
            ctx.set_name(flask.request.form.get('name'))
            ctx.set_title(flask.request.form.get('title'))
            ctx.set_code(flask.request.form.get('code'))
        return flask.redirect(
            flask.url_for('.display', templatename=template['name']))

    elif utils.http_DELETE():
        cnx = dbportal.system.get_cnx(write=True)
        with cnx:
            sql = "DELETE FROM templates WHERE name=?"
            cnx.execute(sql, (template['name'],))
        return flask.redirect(flask.url_for('templates.owner',
                                            username=template['owner']))

@blueprint.route('/<name:templatename>/clone', methods=['GET', 'POST'])
@dbportal.user.login_required
def clone(templatename):
    "Create a clone of the template."
    try:
        template = get_check_read(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))

    if utils.http_GET():
        return flask.render_template('template/clone.html', template=template)

    elif utils.http_POST():
        try:
            with TemplateContext() as ctx:
                name = flask.request.form['name']
                ctx.set_name(name)
                ctx.set_title(flask.request.form.get('title'))
                ctx.set_type(template['type'])
                ctx.set_code(template['code'])
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', name=templatename))
        return flask.redirect(
            flask.url_for('.display', templatename=ctx.template['name']))

@blueprint.route('/<name:templatename>/public', methods=['POST'])
@dbportal.user.login_required
def public(templatename):
    "Set the template to public access."
    utils.check_csrf_token()
    try:
        template = get_check_write(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))
    try:
        with TemplateContext(template) as ctx:
            ctx.template['public'] = True
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Template set to public access.', 'message')
    return flask.redirect(
        flask.url_for('.display', templatename=template['name']))

@blueprint.route('/<name:templatename>/private', methods=['POST'])
@dbportal.user.login_required
def private(templatename):
    "Set the template to private access."
    utils.check_csrf_token()
    try:
        template = get_check_write(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))
    try:
        with TemplateContext(template) as ctx:
            ctx.template['public'] = False
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Template public access revoked.', 'message')
    return flask.redirect(
        flask.url_for('.display', templatename=template['name']))

@blueprint.route('/<name:templatename>/field', methods=['GET', 'POST'])
@dbportal.user.login_required
def field(templatename):
    "Add an input field to the template definition."
    try:
        template = get_check_write(templatename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))

    if utils.http_GET():
        return flask.render_template('template/field_add.html',
                                     template=template)

    elif utils.http_POST():
        try:
            with TemplateContext(template) as ctx:
                ctx.add_field_from_form()
        except ValueError as error:
            flask.flash(str(error), 'error')
        return flask.redirect(
            flask.url_for('.display', templatename=template['name']))

@blueprint.route('/<name:templatename>/field/<name:fieldname>',
                 methods=['GET', 'POST', 'DELETE'])
@dbportal.user.login_required
def field_edit(templatename, fieldname):
    "Edit the input field in the template definition. Or delete it."
    try:
        template = get_check_write(templatename)
        if fieldname not in template['fields']:
            raise ValueError('no such field in template')
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates.public'))

    if utils.http_GET():
        return flask.render_template('template/field_edit.html',
                                     template=template,
                                     field=template['fields'][fieldname])

    elif utils.http_POST():
        try:
            with TemplateContext(template) as ctx:
                ctx.edit_field_from_form(fieldname)
        except ValueError as error:
            flask.flash(str(error), 'error')
        return flask.redirect(
            flask.url_for('.display', templatename=template['name']))

    elif utils.http_DELETE():
        with TemplateContext(template) as ctx:
            ctx.remove_field(fieldname)
        return flask.redirect(
            flask.url_for('.display', templatename=template['name']))

@blueprint.route('/select/<name:dbname>/<name:sourcename>',
                 methods=['GET', 'POST'])
@dbportal.user.login_required
def select(dbname, sourcename):
    "Select a template to use for the table or view."
    try:
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbportal.db.get_schema(db, sourcename)
    except KeyError:
        flask.flash('no such table or view', 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if utils.http_GET():
        templates = get_templates(owner=flask.g.current_user['username'],
                                  public=True)
        return flask.render_template('template/select.html',
                                     db=db,
                                     schema=schema,
                                     templates=templates)

    elif utils.http_POST():
        try:
            template = get_check_read(flask.request.form.get('template'))
        except ValueError as error:
            flask.flash(str(error), 'error')
            url = utils.url_for_rows(db, schema)
        else:
            url = flask.url_for('.render',
                                templatename=template['name'],
                                dbname=db['name'],
                                sourcename=schema['name'])
        return flask.redirect(url)

@blueprint.route('/render/<name:templatename>/<name:dbname>/<name:sourcename>',
                 methods=['GET', 'POST'])
@dbportal.user.login_required
def render(templatename, dbname, sourcename):
    "Create a visualization of the table or view using the given template."
    try:
        template = get_check_read(templatename)
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbportal.db.get_schema(db, sourcename)
    except KeyError:
        flask.flash('no such table or view', 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if utils.http_GET():
        fields = list(template['fields'].values())
        fields.sort(key=lambda f: f['ordinal'])
        return flask.render_template('template/render.html',
                                     db=db,
                                     schema=schema,
                                     template=template,
                                     fields=fields)

    elif utils.http_POST():
        visualname = flask.request.form.get('_visualname')
        try:
            if not visualname:
                raise ValueError('no visual name given')
            if not constants.NAME_RX.match(visualname):
                raise ValueError('invalid visual name')
            visualname = visualname.lower()
            try:
                dbportal.db.get_visual(db, visualname)
            except ValueError:
                pass
            else:
                raise ValueError('visualization name already in use')
            context = {'DATA_URL': utils.url_for_rows(db,
                                                      schema,
                                                      external=True,
                                                      csv=True),
                       'TITLE': f"{template['title'] or template['name']}" +
                                f" of {schema['type']} {schema['name']}"}
            for field in template['fields'].values():
                colname = flask.request.form.get(field['name']) or None
                if colname is None:
                    if not field['optional']:
                        raise ValueError(f"missing value for {field['name']}")
                else:
                    context[field['name']] = colname
            strspec = jinja2.Template(template['code']).render(**context)
            spec = json.loads(strspec)
            if template['type'] == constants.VEGA:
                jsonschema.validate(
                    instance=spec,
                    schema=flask.current_app.config['VEGA_SCHEMA'])
            elif template['type'] == constants.VEGA_LITE:
                jsonschema.validate(
                    instance=spec,
                    schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_visual(visualname, schema['name'], spec)
        except (ValueError, TypeError, jinja2.TemplateError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.render',
                                                templatename=templatename,
                                                dbname=dbname,
                                                sourcename=sourcename))
        return flask.redirect(flask.url_for('visual.display',
                                            dbname=db['name'],
                                            visualname=visualname))

class TemplateContext:
    "Context handler to create, modify and save a template."

    def __init__(self, template=None):
        if template is None:
            self.template = {'owner':   flask.g.current_user['username'],
                             'fields': {},
                             'code': '',
                             'public':  False,
                             'created': utils.get_time()}
            self.old = {}
        else:
            self.template = template
            self.old = copy.deepcopy(template)

    @property
    def cnx(self):
        try:
            return self._cnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._cnx = dbportal.system.get_cnx(write=True)
            return self._cnx

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['name', 'owner']:
            if not self.template.get(key):
                raise ValueError(f"invalid template: {key} not set")
        self.template['modified'] = utils.get_time()
        with self.cnx:
            # Update existing template entry in the system database
            if self.old:
                sql = "UPDATE templates SET name=?, owner=?, title=?, code=?," \
                      " type=?, fields=?, public=?, modified=? WHERE name=?"
                self.cnx.execute(sql, (self.template['name'],
                                       self.template['owner'],
                                       self.template.get('title'),
                                       self.template['code'],
                                       self.template['type'],
                                       json.dumps(self.template['fields']),
                                       bool(self.template['public']),
                                       self.template['modified'],
                                       self.old['name']))
            # Create template entry in the system database
            else:
                sql = "INSERT INTO templates" \
                      " (name, owner, title, code, type, fields, public," \
                      "  created, modified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.template['name'],
                                       self.template['owner'],
                                       self.template.get('title'),
                                       self.template['code'], 
                                       self.template['type'], 
                                       json.dumps(self.template['fields']),
                                       bool(self.template['public']),
                                       self.template['created'], 
                                       self.template['modified']))

    def set_name(self, name):
        "Set or change the template name."
        if name == self.template.get('name'): return
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid template name')
        name = name.lower()
        if get_template(name):
            raise ValueError('template name already in use')
        self.template['name'] = name

    def set_title(self, title):
        "Set the template title."
        self.template['title'] = title or None

    def set_type(self, type):
        "Set the template type."
        if type not in constants.TEMPLATE_TYPES:
            raise ValueError('invalid template type')
        self.template['type'] = type

    def set_code(self, code):
        "Set the template code."
        self.template['code'] = code or ''

    def add_field_from_form(self):
        "Add a field from data in the request form."
        name = flask.request.form.get('name')
        if not name:
            raise ValueError('no name provided for field')
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid name for field')
        name = name.lower()
        if name in self.template['fields']:
            raise ValueError('field name already in use')
        field = {'name': name}
        field['types'] = flask.request.form.getlist('type')
        if set(field['types']).difference(constants.COLUMN_TYPES):
            raise ValueError('invalid type provided for field')
        field['title'] = flask.request.form.get('title') or None
        field['description'] = flask.request.form.get('description') or None
        field['optional'] = utils.to_bool(flask.request.form.get('optional'))
        field['ordinal'] = len(self.template['fields'])
        self.template['fields'][field['name']] = field

    def edit_field_from_form(self, fieldname):
        "Edit the field by data in the request form."
        field = self.template['fields'][fieldname]
        field['types'] = flask.request.form.getlist('type')
        if set(field['types']).difference(constants.COLUMN_TYPES):
            raise ValueError('invalid type provided for field')
        field['title'] = flask.request.form.get('title') or None
        field['description'] = flask.request.form.get('description') or None
        field['optional'] = utils.to_bool(flask.request.form.get('optional'))
        try:
            ordinal = int(flask.request.form.get('ordinal'))
        except (ValueError, TypeError):
            pass
        else:
            fields = list(self.template['fields'].values())
            if ordinal < field['ordinal']:
                for field in fields:
                    if field['ordinal'] >= ordinal: field['ordinal'] += 1
            elif ordinal > field['ordinal']:
                for field in fields:
                    if field['ordinal'] <= ordinal: field['ordinal'] -= 1
            field['ordinal'] = ordinal
        self.renumber_fields()

    def remove_field(self, fieldname):
        "Remove the field with the given name, and renumber the remaining ones."
        self.template['fields'].pop(fieldname)
        self.renumber_fields()

    def renumber_fields(self):
        fields = list(self.template['fields'].values())
        fields.sort(key=lambda f: f['ordinal'])
        for ordinal, field in enumerate(fields):
            field['ordinal'] = ordinal


def get_templates(public=None, owner=None):
    "Get the list of templates according to criteria."
    sql = "SELECT name FROM templates"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' OR '.join(criteria.keys())
    sql += ' ORDER BY name'
    cursor = dbportal.system.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [get_template(row[0]) for row in cursor]

def get_template(templatename):
    """Return the template for the given name.
    Return None if no such template.
    """
    cursor = dbportal.system.get_cursor()
    sql = "SELECT owner, title, description, code, type, fields, public," \
          " created, modified FROM templates WHERE name=?"
    cursor.execute(sql, (templatename,))
    rows = cursor.fetchall()
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    template = {'name':       templatename,
                'owner':      row[0],
                'title':      row[1],
                'description':row[2],
                'code':       row[3],
                'type':       row[4],
                'fields':     json.loads(row[5]),
                'public':     bool(row[6]),
                'created':    row[7],
                'modified':   row[8]}
    return template

def get_check_read(templatename):
    """Get the template and check that
    the current user has read access.
    Raise ValueError if any problem."""
    template = get_template(templatename)
    if template is None:
        raise ValueError('no such template')
    if not has_read_access(template):
        raise ValueError('you may not read the template')
    return template

def has_read_access(template):
    "Does the current user (if any) have read access to the template?"
    if template['public']: return True
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == template['owner']

def get_check_write(templatename):
    """Get the template and check that
    the current user has write access.
    Raise ValueError if any problem."""
    template = get_template(templatename)
    if template is None:
        raise ValueError('no such template')
    if not has_write_access(template):
        raise ValueError('you may not write the template')
    return template

def has_write_access(template):
    "Does the current user (if any) have write access to the template?"
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == template['owner']
