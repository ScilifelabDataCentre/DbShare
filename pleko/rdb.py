"Relational database resource (rdb). Flask blueprint."

import flask

import pleko.constants
import pleko.utils
from pleko.user import (get_current_user,
                        login_required,
                        admin_required)


blueprint = flask.Blueprint('rdb', __name__)

@blueprint.route('/', methods=["GET", "POST"])
def view(rid):
    "View the rdb resource."
    raise NotImplementedError
