"Visualization template endpoints."

import json

import flask
import sqlite3

import pleko.db
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('template', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@pleko.user.login_required
def create():
    "Create a template."
    if utils.is_method_GET():
        return flask.render_template('template/create.html')

    elif utils.is_method_POST():
        try:
            with TemplateContext() as ctx:
                ctx.set_name(flask.request.form.get('name'))
                ctx.set_title(flask.request.form.get('title'))
                ctx.set_type(flask.request.form.get('type'))
                ctx.set_code(flask.request.form.get('code'))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create'))
        return flask.redirect(flask.url_for('.view',
                                            templatename=ctx.template['name']))

@blueprint.route('/<name:templatename>')
@pleko.user.login_required
def view(templatename):
    "View the template definition."
    try:
        template = get_template(templatename)
        if template is None:
            raise ValueError('no such template')
        if not has_read_access(template):
            raise ValueError('may not read the templat')
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('templates'))
    return flask.render_template('template/view.html', template=template)

@blueprint.route('/<name:templatename>/edit')
@pleko.user.login_required
def edit(templatename):
    "Edit the template definition."
    raise NotImplementedError

@blueprint.route('/<name:templatename>/field')
@pleko.user.login_required
def field(templatename):
    "Add an input field to the template definition."
    raise NotImplementedError

@blueprint.route('/<name:templatename>/render/<name:dbname>/<name:sourcename>')
@pleko.user.login_required
def render(templatename):
    "Render the given source (table or view) with the given template."
    raise NotImplementedError


class TemplateContext:
    "Context handler to create, modify and save a visualization template."

    def __init__(self, template=None):
        if template is None:
            self.template = {'owner':   flask.g.current_user['username'],
                             'code': '',
                             'fields': {},
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
            self._cnx = pleko.master.get_cnx(write=True)
            return self._cnx

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['name', 'owner']:
            if not self.template.get(key):
                raise ValueError("invalid template: %s not set" % key)
        self.template['modified'] = utils.get_time()
        if not self.old and get_template(self.template['name']):
            raise ValueError('template name already in use')
        with self.cnx:
            # Update existing template entry in master
            if self.old:
                sql = "UPDATE templates SET owner=?, title=?, code=?," \
                      " type=?, fields=?, public=?, modified=? WHERE name=?"
                self.cnx.execute(sql, (self.template['owner'],
                                       self.template.get('title'),
                                       self.template['code'],
                                       self.template['type'],
                                       json.dumps(self.template['fields']),
                                       bool(self.template['public']),
                                       self.template['modified'],
                                       self.template['name']))
            # Create template entry in master
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
        "Set or change the visualization template name."
        if name == self.template.get('name'): return
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid template name')
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
        self.template['code'] = code


def get_templates(public=None, owner=None):
    "Get the list of templates according to criteria."
    sql = "SELECT name FROM templates"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' AND '.join(criteria.keys())
    cursor = pleko.master.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [get_template(row[0]) for row in cursor]

def get_template(name):
    """Return the database metadata for the given name.
    Return None if no such database.
    """
    cursor = pleko.master.get_cursor()
    sql = "SELECT owner, title, description, code, type, fields, public," \
          " created, modified FROM templates WHERE name=?"
    cursor.execute(sql, (name,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    template = {'name':       name,
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

def has_read_access(template):
    "Does the current user (if any) have read access to the template?"
    if template['public']: return True
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == template['owner']
