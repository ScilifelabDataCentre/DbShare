"Pleko plot endpoints."

import copy
import itertools
import json
import re
import sqlite3
import urllib.parse

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
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('plot/home.html',
                                 db=db,
                                 has_write_access=pleko.db.has_write_access(db))

@blueprint.route('/<name:dbname>/display/<nameext:plotname>')
def display(dbname, plotname): # NOTE: plotname is a NameExt instance!
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot(db, str(plotname))
        schema = pleko.db.get_schema(db, plot['sourcename'])
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
                            for tc in PLOTS_TEMPLATES.values()])
        return flask.render_template('plot/select.html',
                                     db=db,
                                     plottypes=plottypes,
                                     type=flask.request.args.get('type'),
                                     sourcename=flask.request.args.get('sourcename'))

    elif utils.is_method_POST():
        try:
            template = PLOTS_TEMPLATES.get(flask.request.form.get('type'))
            if not template:
                raise ValueError('no such plot type')
            schema = pleko.db.get_schema(
                db, flask.request.form.get('sourcename'))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.select', dbname=dbname))
        return flask.redirect(flask.url_for('.create',
                                            dbname=db['name'],
                                            plottype=template.type(),
                                            sourcename=schema['name']))

@blueprint.route('/<name:dbname>/create/<name:plottype>/<name:sourcename>',
                 methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, plottype, sourcename):
    "Create a plot of the given type for the given table/view."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        templateclass = PLOTS_TEMPLATES.get(plottype)
        if not templateclass:
            raise ValueError('no such plot type')
        schema = pleko.db.get_schema(db, sourcename)
        if schema['type'] == constants.TABLE:
            data_url = utils.get_url('table.rows',
                                     values=dict(dbname=dbname, 
                                                 tablename=sourcename))
        elif schema['type'] == constants.VIEW:
            data_url = utils.get_url('view.rows',
                                     values=dict(dbname=dbname, 
                                                 viewname=sourcename))
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
            plotname = flask.request.form.get('_name')
            if not plotname:
                raise ValueError('no plot name given')
            if not constants.NAME_RX.match(plotname):
                raise ValueError('invalid plot name')
            plotname = plotname.lower()
            try:
                get_plot(db, plotname)
            except ValueError:
                pass
            else:
                raise ValueError('plot name already in use')
            template.set(flask.request.form)
            spec = json.loads(str(template))
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
            with pleko.db.DbContext(db) as ctx:
                with ctx.dbcnx:
                    sql = "INSERT INTO %s (name, sourcename, type, spec)" \
                          " VALUES (?, ?, ?, ?)" % constants.PLOTS
                    ctx.dbcnx.execute(sql, (plotname,
                                            schema['name'],
                                            template.type(),
                                            json.dumps(spec)))
        except (ValueError, TypeError,
                sqlite3.Error, jsonschema.ValidationError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                utils.get_url('.create',
                              values=dict(dbname=dbname,
                                          plottype=template.type(),
                                          sourcename=sourcename)))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=plotname))

@blueprint.route('/<name:dbname>/edit/<name:plotname>', 
                 methods=['GET', 'POST', 'DELETE'])
@pleko.user.login_required
def edit(dbname, plotname):
    "Edit the plot."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot(db, plotname)
        schema = pleko.db.get_schema(db, plot['sourcename'])
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
        try:
            newname = flask.request.form.get('name') or plotname
            strspec = flask.request.form.get('spec')
            if not newname:
                raise ValueError('no plot name given')
            if not constants.NAME_RX.match(newname):
                raise ValueError('invalid plot name')
            newname = newname.lower()
            if newname != plotname:
                try:
                    get_plot(db, newname)
                except ValueError:
                    pass
                else:
                    raise ValueError('plot name already in use')
            if not strspec:
                raise ValueError('no spec given')
            spec = json.loads(strspec)
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
            with pleko.db.DbContext(db) as ctx:
                ctx.update_plot(plotname, spec, newname)
                # with ctx.dbcnx:
                #     sql = "UPDATE %s SET name=?, spec=? WHERE name=?" % \
                #                                constants.PLOTS
                #     ctx.dbcnx.execute(sql, (newname, json.dumps(spec),plotname))
        except (ValueError, TypeError,
                sqlite3.Error, jsonschema.ValidationError) as error:
            flask.flash(str(error), 'error')
            return flask.render_template('plot/edit.html', 
                                         db=db,
                                         plot=plot,
                                         spec=strspec, # Spec maybe with errors
                                         schema=schema)
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=newname))

    elif utils.is_method_DELETE():
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_plot(plotname)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

@blueprint.route('/<name:dbname>/clone/<name:plotname>', methods=['GET','POST'])
@pleko.user.login_required
def clone(dbname, plotname):
    "Clone the plot."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        plot = get_plot(db, plotname)
        schema = pleko.db.get_schema(db, plot['sourcename'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/clone.html', db=db, plot=plot)

    elif utils.is_method_POST():
        try:
            plotname = flask.request.form.get('name')
            if not plotname:
                raise ValueError('no plot name given')
            if not constants.NAME_RX.match(plotname):
                raise ValueError('invalid plot name')
            plotname = plotname.lower()
            try:
                get_plot(db, plotname)
            except ValueError:
                pass
            else:
                raise ValueError('plot name already in use')
            with pleko.db.DbContext(db) as ctx:
                with ctx.dbcnx:
                    sql = "INSERT INTO %s (name, sourcename, type, spec)" \
                          " VALUES (?, ?, ?, ?)" % constants.PLOTS
                    ctx.dbcnx.execute(sql, (plotname,
                                            schema['name'],
                                            plot['type'],
                                            json.dumps(plot['spec'])))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=plotname))

def get_plot(db, plotname):
    # db['plots'] has source name as key and plot lists as values.
    for plot in itertools.chain.from_iterable(db['plots'].values()):
        if plot['name'] == plotname: return plot
    raise ValueError('no such plot')


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


PLOTS_TEMPLATES = dict([(tc.type(), tc) for tc in [Scatterplot, Spec]])
