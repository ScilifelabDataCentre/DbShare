"""Pleko plot endpoints.

/plot/<dbname>
  List of plots.

/plot/<dbname>/display/<plotname>
  Display.

/plot/<dbname>/create/<tableviewname>
  Create plot for the given table or view.

/plot/<dbname>/edit/<plotname>
  Edit.
"""

import copy
import json
import sqlite3

import flask

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
        db = pleko.db.get_check_read(dbname, nrows=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('plot/home.html', db=db)

@blueprint.route('/<name:dbname>/display/<name:plotname>')
def display(dbname, plotname):
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname)
        plot = get_plot(dbname, plotname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('plot/display.html', db=db, plot=plot)

@blueprint.route('/<name:dbname>/create/<name:tableviewname>',
                 methods=['GET', 'POST'])
def create(dbname, tableviewname):
    "Create a plot for the given table or view."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tableviewname]
        schema['type'] = 'table'
    except KeyError:
        try:
            schema = db['views'][tableviewname]
            schema['type'] = 'view'
        except KeyError:
            flask.flash('no such table or view', 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/create.html',
                                     db=db,
                                     schema=schema)
    elif utils.is_method_POST():
        try:
            with PlotContext(db, tableviewname) as ctx:
                ctx.set_plotname(flask.request.form.get('name'))
                ctx.set_spec(flask.request.form.get('spec'))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

def get_plots(dbname):
    """Get the plots for the database.
    List of tuples (tableviewname, plotlist), sorted by table/view and name.
    """
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT name, tableviewname, spec FROM %s" % pleko.db.PLOT_TABLE_NAME
    cursor.execute(sql)
    plots = {}
    for row in cursor:
        plot = {'name': row[0],
                'tableviewname': row[1],
                'spec': json.loads(row[2])}
        plots.setdefault(plot['tableviewname'], []).append(plot)
    for plotlist in plots.values():
        plotlist.sort(key=lambda p: p['name'])
    return sorted(plots.items())
    
def get_plot(dbname, plotname):
    "Get a plot for the database."
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT tableviewname, spec FROM %s WHERE name=?" \
          % pleko.db.PLOT_TABLE_NAME
    cursor.execute(sql, (plotname,))
    rows = list(cursor)
    if len(rows) != 1:
        raise ValueError('no such plot')
    row = rows[0]
    return {'name': plotname,
            'tableviewname': row[0],
            'spec': json.loads(row[1])}


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, db, tableviewname, plot=None):
        self.db = db
        self.tableviewname = tableviewname
        if plot:
            self.plot = copy.deepcopy(plot)
        else:
            self.plot = {}

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        with self.dbcnx:
            if self.plot.get('tableviewname'): # Already exists; update spec
                sql = "UPDATE %s SET spec=? WHERE name=?" % \
                      pleko.db.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (json.dumps(self.plot),
                                         self.plot['name']))
            else:               # Insert into table
                sql = "INSERT INTO %s (name, tableviewname, spec)" \
                      " VALUES(?, ?, ?)" % pleko.db.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         self.tableviewname,
                                         json.dumps(self.plot['spec'])))

    @property
    def dbcnx(self):
        try:
            return self._dbcnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._dbcnx = pleko.db.get_cnx(self.db['name'], write=True)
            return self._dbcnx

    def set_plotname(self, plotname):
        "Set the plot name."
        if not plotname:
            raise ValueError('no plot name given')
        if not constants.NAME_RX.match(plotname):
            raise ValueError('invalid plot name')
        if self.plot.get('name'):
            raise ValueError('cannot change the plot name')
        self.plot['name'] = plotname

    def set_tableviewname(self, tableviewname):
        if not tableviewname:
            raise ValueError('no table name given')
        if not constants.NAME_RX.match(tableviewname):
            raise ValueError('invalid table name')
        if self.plot.get('tableviewname'):
            raise ValueError('cannot change the tableviewname of the plot')
        self.plot['tableviewname'] = tableviewname

    def set_spec(self, spec):
        try:
            self.plot['spec'] = json.loads(spec)
            # XXX Check Vega-Lite JSON-Schema
        except (ValueError, TypeError) as error:
            raise ValueError(str(error))
