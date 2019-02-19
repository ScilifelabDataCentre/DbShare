"Auth blueprint."

import flask
import werkzeug.security

from pleko import utils


auth_blueprint = flask.Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=["GET", "POST"])
def login():
    "Login to a user account."
    if utils.is_method_GET():
        return flask.render_template('login.html')
    if utils.is_method_POST():
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        try:
            if username and password:
                try:
                    user = flask.g.userdb[username]
                except KeyError:
                    raise ValueError
                if not werkzeug.security.check_password_hash(user['password'],
                                                             password):
                    raise ValueError
                flask.session['username'] = user['username']
                flask.session.permanent = True
            else:
                raise ValueError
            try:
                return flask.redirect(flask.request.form['next'])
            except KeyError:
                return flask.redirect(flask.url_for('index'))
        except ValueError:
            flask.flash('invalid user or password', 'error')
            return flask.redirect(flask.url_for('login'))

@auth_blueprint.route('/logout', methods=["POST"])
def logout():
    "Logout from the user account."
    del flask.session['username']
    return flask.redirect(flask.url_for('index'))
