"Pleko plot endpoints."

import copy
import itertools
import json
import sqlite3

import flask
import jsonschema

import pleko.db
import pleko.master
import pleko.user
from pleko import constants
from pleko import utils


class Template:
    "Base plot specification template."

    template = {
        "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
        "title": "Plot title",
        "width": 400,
        "height": 400,
        "description": "Plot description.",
        "data": {
            "url": None
        }
    }

    fields = [{'name': 'title',
               'label': 'Title',
               'type': 'text'},
              {'name': 'description',
               'label': 'Description',
               'type': 'textarea'}]

    def __init__(self, spec=None):
        if spec:
            self.spec = copy.deepcopy(spec)
        else:
            self.spec = copy.deepcopy(self.template)

    def __str__(self):
        return json.dumps(self.spec, indent=2)

    @property
    def type(self): return self.__class__.__name__.lower()

    @property
    def description(self): return self.__class__.__doc__

    def from_form(self):
        for field in self.fields:
            setter = getattr(self, "set_%s" % field['name'])
            setter(flask.request.form.get(field['name']))

    def set_title(self, value):
        self.spec['title'] = value

    def set_description(self, value):
        self.spec['description'] = value

    def check_validity(self):
        """Check that all required values have been set.
        Raise ValueError otherwise.
        """
        pass

    def update_data_url(self, db, tableviewname):
        schema = pleko.db.get_schema(db, tableviewname)
        if schema['type'] == 'table':
            url = utils.get_url('table.rows',
                                values=dict(dbname=db['name'],
                                            tablename=tableviewname))
        elif schema['type'] == 'view':
            url = utils.get_url('view.rows',
                                values=dict(dbname=db['name'],
                                            tablename=tableviewname))
        else:
            raise NotImplementedError
        self.spec['data']['url'] = url + '.csv'


class Spec(Template):
    "Vega-Lite JSON specification."

    fields = copy.deepcopy(Template.fields)
    fields.extend([{'name': 'spec',
                    'label': 'Vega-Lite spec',
                    'info_url': 'VEGALITE_URL',
                    'type': 'textarea',
                    'rows': 24}])

    def set_spec(self, value):
        "Replace the spec completely by the incoming value"
        if isinstance(spec, dict):
            self.spec = copy.deepcopy(spec)
        else:
            try:
                self.spec = json.loads(spec)
            except (ValueError, TypeError) as error:
                raise ValueError(str(error))


class PreparedTemplate(Template):
    "Template for prepared plots."

    fields = copy.deepcopy(Template.fields)
    fields.extend([{'name': 'width', 
                    'label': 'Plot width (px)',
                    'type': 'integer',
                    'grid': 2,
                    'default': 400},
                   {'name': 'height', 
                    'label': 'Plot height (px)',
                    'type': 'integer',
                    'grid': 2,
                    'default': 400}])
                   
    def set_width(self, value):
        self.spec['width'] = int(value)
    def set_height(self, value):
        self.spec['height'] = int(value)


class Scatterplot(PreparedTemplate):
    """Scatterplot of two quantitative variables,
    optionally with color and shape nominal variables."""

    template = copy.deepcopy(PreparedTemplate.template)
    template.update({
        "mark": "point",
        "encoding": {
            "x": {"field": None, "type": "quantitative"},
            "y": {"field": None, "type": "quantitative"},
            "color": {"field": None, "type": "nominal"},
            "shape": {"field": None, "type": "nominal"}
        }
    })

    fields = copy.deepcopy(PreparedTemplate.fields)
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

    def set_x(self, value):
        if not value:
            raise ValueError("invalid value for 'x'")
        self.spec['encoding']['x']['field'] = value
    def set_y(self, value):
        if not value:
            raise ValueError("invalid value for 'y'")
        self.spec['encoding']['y']['field'] = value
    def set_color(self, value):
        self.spec['encoding']['color']['field'] = value or None
    def set_shape(self, value):
        self.spec['encoding']['shape']['field'] = value or None


PLOT_TEMPLATES = dict([(t.type, t) for t in [Scatterplot(), Spec()]])


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
def display(dbname, plotname):
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname, nrows=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot(dbname, str(plotname))
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

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
        plottypes = sorted([(t.type, t.description) 
                            for t in PLOT_TEMPLATES.values()])
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
                                            plottype=template.type,
                                            tableviewname=schema['name']))

@blueprint.route('/<name:dbname>/create/<name:plottype>/<name:tableviewname>',
                 methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, plottype, tableviewname):
    "Create a plot of the given type for the given table/view."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
        template = copy.deepcopy(PLOT_TEMPLATES.get(plottype))
        if not template:
            raise ValueError('no such plot type')
        schema = pleko.db.get_schema(db, tableviewname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

    if utils.is_method_GET():
        schema['nrows'] = pleko.db.get_nrows(schema['name'],
                                             pleko.db.get_cnx(dbname))
        template.update_data_url(db, tableviewname)
        return flask.render_template('plot/create.html',
                                     db=db,
                                     template=template,
                                     schema=schema,
                                     initial=dict(spec=str(template)))

    elif utils.is_method_POST():
        try:
            with PlotContext(db, tableviewname=tableviewname) as ctx:
                ctx.set_name(flask.request.form.get('_name'))
                ctx.set_type(template.type)
                template.from_form()
                template.update_data_url(db, tableviewname)
                template.check_validity()
                ctx.set_spec(template.spec)
        except (ValueError, TypeError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                utils.get_url('.create',
                              values=dict(dbname=dbname,
                                          plottype=template.type,
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
        return flask.redirect(flask.url_for('db.contents', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/edit.html', 
                                     db=db,
                                     plot=plot,
                                     schema=schema)
    elif utils.is_method_POST():
        try:
            with PlotContext(db, plot=plot) as ctx:
                spec = flask.request.form.get('spec')
                if not spec: raise ValueError('no spec given')
                spec = json.loads(spec)
                ctx.set_spec(spec)
                ctx.set_name(flask.request.form.get('name'))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            plot['spec'] = spec # This is the spec with error(s)
            return flask.render_template('plot/edit.html', 
                                         db=db,
                                         plot=plot,
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
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.contents', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/clone.html', db=db, plot=plot)

    elif utils.is_method_POST():
        try:
            with PlotContext(db, tableviewname=plot['tableviewname']) as ctx:
                ctx.set_name(flask.request.form.get('name'))
                ctx.set_type(plot['type'])
                ctx.set_spec(plot['spec'])
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.contents', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

def get_plots(dbname):
    """Get the plots for the database.
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


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, db, plot=None, tableviewname=None):
        self.db = db
        if plot:
            self.plot = copy.deepcopy(plot)
            self.oldname = plot['name']
            self.tableviewname = self.plot['tableviewname']
        else:
            self.plot = {}
            self.oldname = None
            self.tableviewname = tableviewname

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        if not self.plot.get('name'):
            raise ValueError('plot has no name')
        with self.dbcnx:
            if self.oldname:    # Update already existing plot
                sql = "UPDATE %s SET name=?, spec=? WHERE name=?" % \
                      constants.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         json.dumps(self.plot['spec']),
                                         self.oldname))
            else:               # Insert into table
                sql = "INSERT INTO %s (name, tableviewname, type, spec)" \
                      " VALUES(?, ?, ?, ?)" % constants.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         self.tableviewname,
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
        try:
            if name != self.oldname:
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
        if not type:
            raise ValueError('no plot type given')
        if type not in PLOT_TEMPLATES:
            raise ValueError('no such plot type')
        self.plot['type'] = type

    def set_tableviewname(self, tableviewname):
        if not tableviewname:
            raise ValueError('no table name given')
        if not constants.NAME_RX.match(tableviewname):
            raise ValueError('invalid table name')
        if self.plot.get('tableviewname'):
            raise ValueError('cannot change the tableviewname of the plot')
        self.plot['tableviewname'] = tableviewname

    def set_spec(self, spec):
        """Set the Vega-Lite specification of the plot.
        Raise ValueError if it is invalid.
        """
        try:
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
        except jsonschema.ValidationError as error:
            raise ValueError(str(error))
        self.plot['spec'] = spec
