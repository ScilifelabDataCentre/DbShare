"Database API endpoints."

import http.client
import io

import flask
import jsonschema

import dbshare.db
import dbshare.api.schema
import dbshare.api.table
import dbshare.api.user
import dbshare.api.view

from .. import constants
from .. import utils

blueprint = flask.Blueprint('api_db', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def database(dbname):
    """GET: List the database tables, views and metadata.
    PUT: Create the database.
    POST: Edit the database metadata.
    DELETE: Delete the database.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname, nrows=True)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        return utils.jsonify(utils.get_json(**get_json(db, complete=True)),
                             schema='/db')
 
    elif utils.http_PUT():
        db = dbshare.db.get_db(dbname)
        if db is not None:
            utils.abort_json(http.client.FORBIDDEN, 'database exists')
        try:
            if flask.request.content_length:
                db = dbshare.db.add_database(
                    dbname,
                    infile=io.BytesIO(flask.request.get_data()),
                    size=flask.request.content_length)
            else:
                with dbshare.db.DbContext() as ctx:
                    ctx.set_name(dbname)
                    ctx.initialize()
                db = ctx.db
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for('api_db.database', dbname=dbname))

    elif utils.http_POST(csrf=False):
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            data = flask.request.get_json()
            utils.json_validate(data, dbshare.schema.db.edit)
            with dbshare.db.DbContext(db) as ctx:
                try:
                    ctx.set_name(data['name'])
                except KeyError:
                    pass
                try:
                    ctx.set_title(data['title'])
                except KeyError:
                    pass
                try:
                    ctx.set_description(data['description'])
                except KeyError:
                    pass
                try:
                    ctx.set_public(data['public'])
                except KeyError:
                    pass
        except (jsonschema.ValidationError, ValueError) as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for('api_db.database', dbname=db['name']))

    elif utils.http_DELETE(csrf=False):
        try:
            dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        dbshare.db.delete_database(dbname)
        return ('', http.client.NO_CONTENT)

@blueprint.route('/<name:dbname>/readonly', methods=['POST'])
def readonly(dbname):
    "POST: Set the database to read-only."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if not db['readonly']:
            with dbshare.db.DbContext(db) as ctx:
                ctx.set_readonly(True)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for('api_db.database', dbname=dbname))

@blueprint.route('/<name:dbname>/readwrite', methods=['POST'])
def readwrite(dbname):
    "POST: Set the database to read-write."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if db['readonly']:
            with dbshare.db.DbContext(db) as ctx:
                ctx.set_readonly(False)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for('api_db.database', dbname=dbname))

def get_json(db, complete=False):
    "Return the JSON for the database."
    result = {'name': db['name'],
              'title': db.get('title'),
              'description': db.get('description'),
              'owner': dbshare.api.user.get_json(db['owner']),
              'public': db['public'],
              'readonly': db['readonly'],
              'size': db['size'],
              'modified': db['modified'],
              'created': db['created'],
              'hashes': db['hashes']
    }
    if complete:
        result['tables'] = [dbshare.api.table.get_json(db, table)
                            for table in db['tables'].values()]
        result['views'] = [dbshare.api.view.get_json(db, view)
                           for view in db['views'].values()]
        result['operations'] = {}
        if dbshare.db.has_write_access(db):
            result['operations']['edit'] = {
                'title': 'Edit the metadata of the database.',
                'method': 'POST',
                'input': {
                    'contentType': constants.JSON_MIMETYPE,
                    'schema': dbshare.api.schema.schemas['db/edit']['href']
                }
            }
            result['operations']['delete'] = {
                'title': 'Delete the database.',
                'method': 'DELETE'
            }
        if dbshare.db.has_write_access(db, check_mode=False):
            if db['readonly']:
                result['operations']['readwrite'] = {
                    'title': 'Set the database to read-write.',
                    'href': utils.url_for('api_db.readwrite', dbname=db['name']),
                    'method': 'POST'
                }
            else:
                result['operations']['readonly'] = {
                    'title': 'Set the database to read-only.',
                    'href': utils.url_for('api_db.readonly', dbname=db['name']),
                    'method': 'POST'
                }
    return result
