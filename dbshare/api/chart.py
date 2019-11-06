"Chart API endpoints."

import http

import flask
import jsonschema

import dbshare.db
import dbshare.chart

from .. import utils


blueprint = flask.Blueprint('api_chart', __name__)

@blueprint.route('/<name:dbname>/<name:chartname>',
                 methods=['GET', 'PUT', 'DELETE'])
def chart(dbname, chartname):
    """GET: Return the chart information.
    PUT: Create the chart.
    DELETE: Delete the chart.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            chart = db['charts'][chartname]
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        import json
        return utils.jsonify(utils.get_json(**chart), schema='/chart')

    elif utils.http_PUT():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                data = flask.request.get_json()
                schema = dbshare.db.get_schema(db, data['sourcename'])
                template = dbshare.chart.get_template(data['templatename'])
                spec = dbshare.chart.get_chart_spec(template, data)
                ctx.add_chart(chartname, schema, spec)
        except (KeyError, ValueError, jsonschema.ValidationError) as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for('api_chart.chart', dbname=dbname,chartname=chartname))

    elif utils.http_DELETE():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.delete_chart(chartname)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return ('', http.client.NO_CONTENT)
