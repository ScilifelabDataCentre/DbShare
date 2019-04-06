"Pleko plot endpoints."

import copy
import itertools
import json
import sqlite3

import dpath
import flask
import jinja2
import jsonschema

import pleko.db
import pleko.master
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('plot', __name__)

@blueprint.route('/<name:dbname>')
def home(dbname):
    "List the plots in the database."
    try:
        db = pleko.db.get_check_read(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('plot/home.html',
                                 db=db,
                                 has_write_access=pleko.db.has_write_access(db))

@blueprint.route('/<name:dbname>/display/<nameext:plotname>',
                 methods=['GET', 'POST', 'DELETE'])
def display(dbname, plotname): # NOTE: plotname is a NameExt instance!
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot(dbname, str(plotname))
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    schema['nrows'] = pleko.db.get_nrows(schema['name'],
                                         pleko.db.get_cnx(dbname))
    if plotname.ext is None or plotname.ext == 'html':
        return flask.render_template(
            'plot/display.html',
            db=db,
            schema=schema,
            plot=plot,
            has_write_access = pleko.db.has_write_access(db))
    elif plotname.ext == 'json':
        return flask.jsonify(plot['spec'])
    else:
        flask.abort(406)

@blueprint.route('/<name:dbname>/select', methods=['GET', 'POST'])
@pleko.user.login_required
def select(dbname):
    "Select plot type and table/view."
    try:
        db = pleko.db.get_check_write(dbname, nrows=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.is_method_GET():
        plottypes = sorted([(tc.type(), tc.__doc__) 
                            for tc in PLOT_TEMPLATES.values()])
        return flask.render_template('plot/select.html',
                                     db=db,
                                     plottypes=plottypes,
                                     type=flask.request.args.get('type'),
                                     tableviewname=flask.request.args.get('tableviewname'))

    elif utils.is_method_POST():
        try:
            template = PLOT_TEMPLATES.get(flask.request.form.get('type'))
            if not template:
                raise ValueError('no such plot type')
            schema = pleko.db.get_schema(
                db, flask.request.form.get('tableviewname'))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.select', dbname=dbname))
        return flask.redirect(flask.url_for('.create',
                                            dbname=db['name'],
                                            plottype=template.type(),
                                            tableviewname=schema['name']))

@blueprint.route('/<name:dbname>/create/<name:plottype>/<name:tableviewname>',
                 methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, plottype, tableviewname):
    "Create a plot of the given type for the given table/view."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        templateclass = PLOT_TEMPLATES.get(plottype)
        if not templateclass:
            raise ValueError('no such plot type')
        schema = pleko.db.get_schema(db, tableviewname)
        if schema['type'] == constants.TABLE:
            data_url = utils.get_url('table.rows',
                                     values=dict(dbname=dbname, 
                                                 tablename=tableviewname))
        elif schema['type'] == constants.VIEW:
            data_url = utils.get_url('view.rows',
                                     values=dict(dbname=dbname, 
                                                 viewname=tableviewname))
        data_url += '.csv'
        template = templateclass(data_url)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

    if utils.is_method_GET():
        schema['nrows'] = pleko.db.get_nrows(schema['name'],
                                             pleko.db.get_cnx(dbname))
        return flask.render_template('plot/create.html',
                                     db=db,
                                     template=template,
                                     schema=schema)

    elif utils.is_method_POST():
        try:
            with PlotContext(db, schema=schema) as ctx:
                ctx.set_name(flask.request.form.get('_name'))
                template.set(flask.request.form)
                ctx.set_type(template.type())
                ctx.set_spec(str(template))
        except (ValueError, TypeError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                utils.get_url('.create',
                              values=dict(dbname=dbname,
                                          plottype=template.type(),
                                          tableviewname=tableviewname)))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

@blueprint.route('/<name:dbname>/edit/<name:plotname>', 
                 methods=['GET', 'POST', 'DELETE'])
@pleko.user.login_required
def edit(dbname, plotname):
    "Edit the plot."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot_from_db(db, plotname)
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/edit.html', 
                                     db=db,
                                     plot=plot,
                                     spec=json.dumps(plot['spec'], indent=2),
                                     schema=schema)
    elif utils.is_method_POST():
        spec = flask.request.form.get('spec')
        try:
            with PlotContext(db, plot=plot) as ctx:
                ctx.set_name(flask.request.form.get('name'))
                if not spec: raise ValueError('no spec given')
                ctx.set_spec(spec)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.render_template('plot/edit.html', 
                                         db=db,
                                         plot=plot,
                                         spec=spec, # Spec with errors
                                         schema=schema)
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

    elif utils.is_method_DELETE():
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        try:
            with dbcnx:
                sql = "DELETE FROM plot$ WHERE name=?"
                cursor = dbcnx.cursor()
                cursor.execute(sql, (plotname,))
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

@blueprint.route('/<name:dbname>/clone/<name:plotname>', methods=['GET','POST'])
@pleko.user.login_required
def clone(dbname, plotname):
    "Clone the plot."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot_from_db(db, plotname)
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/clone.html', db=db, plot=plot)

    elif utils.is_method_POST():
        try:
            with PlotContext(db, schema=schema) as ctx:
                ctx.set_name(flask.request.form.get('name'))
                ctx.set_type(plot['type'])
                ctx.set_spec(plot['spec'])
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

def get_tableview_plots(dbname):
    """Get the plots for the tables/views in the database.
    Dictionary tableviewname->plotlist.
    """
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT name, tableviewname, type, spec FROM %s" % \
          constants.PLOT_TABLE_NAME
    cursor.execute(sql)
    plots = {}
    for row in cursor:
        plot = {'name': row[0],
                'tableviewname': row[1],
                'type': row[2],
                'spec': json.loads(row[3])}
        plots.setdefault(plot['tableviewname'], []).append(plot)
    return plots
    
def get_plot(dbname, plotname):
    """Get a plot for the database.
    Raise ValueError if no such plot.
    """
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT tableviewname, type, spec FROM %s WHERE name=?" \
          % constants.PLOT_TABLE_NAME
    cursor.execute(sql, (plotname,))
    rows = list(cursor)
    if len(rows) != 1:
        raise ValueError('no such plot')
    row = rows[0]
    return {'name': plotname,
            'tableviewname': row[0],
            'type': row[1],
            'spec': json.loads(row[2])}

def get_plot_from_db(db, plotname):
    # db['plots'] has lists as values.
    for plot in itertools.chain.from_iterable(db['plots'].values()):
        if plot['name'] == plotname: return plot
    raise ValueError('no such plot')

def update_spec_data_urls(dbname, old_dbname):
    """Update the data URLs of the plot specs in the given database.
    To be done after database rename or clone.
    """
    db = pleko.db.get_db(dbname)
    old_table_url = utils.get_url('table.rows',
                                  values=dict(dbname=old_dbname, tablename='x'))
    old_table_url = old_table_url[:-1]
    new_table_url = utils.get_url('table.rows',
                                  values=dict(dbname=dbname, tablename='x'))
    new_table_url = new_table_url[:-1]
    old_view_url = utils.get_url('view.rows',
                                 values=dict(dbname=old_dbname, viewname='x'))
    old_view_url = old_view_url[:-1]
    new_view_url = utils.get_url('view.rows',
                                 values=dict(dbname=dbname, viewname='x'))
    new_view_url = new_view_url[:-1]
    plotlists = get_tableview_plots(dbname).values()
    for plot in [p for plotlist in plotlists for p in plotlist]:
        with PlotContext(db, plot=plot) as ctx:
            spec = plot['spec']
            for path, href in dpath.util.search(spec, 'data/url', yielded=True):
                href = href.replace(old_table_url, new_table_url)
                href = href.replace(old_view_url, new_view_url)
                dpath.util.set(spec, path, href)
            ctx.set_spec(spec)


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, db, plot=None, schema=None):
        self.db = db
        if plot:
            self.plot = copy.deepcopy(plot)
            self.oldname = plot['name']
        else:
            self.plot = {}
            self.oldname = None
        self.schema = schema

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        if not self.plot.get('name'):
            raise ValueError('plot has no name')
        if self.oldname:    # Update already existing plot
            with self.dbcnx:
                sql = "UPDATE %s SET name=?, spec=? WHERE name=?" % \
                      constants.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         json.dumps(self.plot['spec']),
                                         self.oldname))
        else:               # Insert into table
            with self.dbcnx:
                sql = "INSERT INTO %s (name, tableviewname, type, spec)" \
                      " VALUES(?, ?, ?, ?)" % constants.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         self.schema['name'],
                                         self.plot['type'],
                                         json.dumps(self.plot['spec'])))

    @property
    def dbcnx(self):
        try:
            return self._dbcnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._dbcnx = pleko.db.get_cnx(self.db['name'], write=True)
            return self._dbcnx

    def set_name(self, name):
        "Set the plot name."
        if not name:
            raise ValueError('no plot name given')
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid plot name')
        name = name.lower()
        if name != self.oldname:
            try:
                get_plot_from_db(self.db, name)
            except ValueError:
                pass
            else:
                raise ValueError('plot name already in use')
        self.plot['name'] = name

    def set_type(self, type):
        "Set the plot type."
        if self.plot.get('type'):
            raise ValueError('cannot change the plot type')
        if type not in PLOT_TEMPLATES:
            raise ValueError('unknown plot type')
        self.plot['type'] = type

    def set_spec(self, spec):
        "Set the plot spec."
        if isinstance(spec, str):
            spec = json.loads(spec)
        try:
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
        except jsonschema.ValidationError as error:
            raise ValueError(str(error))
        self.plot['spec'] = spec


STANDARD_FIELDS = [{'name': 'title',
                    'label': 'Title',
                    'type': 'text',
                    'optional': True},
                   {'name': 'description',
                    'label': 'Description',
                    'type': 'text',
                    'optional': True},
                   {'name': 'width', 
                    'label': 'Plot width (px)',
                    'type': 'integer',
                    'constraint': 'positive',
                    'grid': 2,
                    'default': 400},
                   {'name': 'height', 
                    'label': 'Plot height (px)',
                    'type': 'integer',
                    'constraint': 'positive',
                    'grid': 2,
                    'default': 400}]

class PlotTemplate:
    "Base plot specification template."

    template = ""
    fields = []

    def __init__(self, data_url):
        self.template = jinja2.Template(self.template)
        self.fields = copy.deepcopy(self.fields)
        self.context = {'data_url': data_url}

    def __str__(self):
        return self.template.render(self.context)

    @classmethod
    def type(cls):
        return cls.__name__.lower()

    def set(self, lookup):
        "Set the field values from the lookup, e.g. flask.request.form"
        for field in self.fields:
            try:
                converter = getattr(self, "convert_%s" % field['name'])
            except AttributeError:
                converter = getattr(self, "convert_%s" % field['type'])
            value = lookup.get(field['name'])
            if value:
                self.context[field['name']] = converter(field, value)
            elif field.get('default'):
                self.context[field['name']] = field.get('default')
            elif field.get('optional'):
                self.context[field['name']] = None
            else:
                raise ValueError("missing value for %s" % field['name'])

    def convert_text(self, field, value):
        return value

    def convert_integer(self, field, value):
        value = int(value)
        if field.get('constraint') == 'positive' and value <= 0:
            raise ValueError
        return value

    def convert_column(self, field, value):
        return value


class Spec(PlotTemplate):
    "Special case: Vega-Lite JSON specification from scratch."

    template = """{
  "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
  "title": "Title",
  "description": "Description",
  "width": 400,
  "height": 400,
  "data": {
    "url": "{{ data_url }}"
  }
}
"""
    fields = [{'name': 'spec',
               'label': 'Vega-Lite spec',
               'info_url': 'VEGALITE_URL',
               'type': 'text',
               'rows': 24}]

    def __init__(self, data_url):
        super().__init__(data_url)
        # This relies on there being only one field.
        self.fields[0]['default'] = self.template.render(self.context)

    def __str__(self):
        "Just the spec value as is."
        return self.context['spec']

    def convert_spec(self, field, value):
        return value


class Scatterplot(PlotTemplate):
    """Scatterplot of two quantitative variables,
    optionally with color and shape nominal variables.
    """

    template = """{
  "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
  "title": "{{ title or ''}}",
  "description": "{{ description or '' }}",
  "width": {{ width }},
  "height": {{ height }},
  "data": {
    "url": "{{ data_url }}"
  },
  "mark": "point",
  "encoding": {
    "x": {
      "field": "{{ x }}",
      "type": "quantitative"
    },
    "y": {
      "field": "{{ y }}",
      "type": "quantitative"
    }
    {% if color %}
    ,"color": {
      "field": "{{ color }}",
      "type": "nominal"
    }
    {% endif %}
    {% if shape %}
    ,"shape": {
      "field": "{{ shape }}",
      "type": "nominal"
    }
    {% endif %}
  }
}"""

    fields = copy.deepcopy(STANDARD_FIELDS)
    fields.extend([{'name': 'x', 
                    'label': 'X-axis',
                    'type': 'column',
                    'grid': 6},
                   {'name': 'y',
                    'label': 'Y-axis',
                    'type': 'column',
                    'grid': 6},
                   {'name': 'color',
                    'label': 'Color',
                    'type': 'column',
                    'grid': 6,
                    'optional': True},
                   {'name': 'shape',
                    'label': 'Shape',
                    'type': 'column',
                    'grid': 6,
                    'optional': True}])


PLOT_TEMPLATES = dict([(tc.type(), tc) for tc in [Scatterplot, Spec]])
