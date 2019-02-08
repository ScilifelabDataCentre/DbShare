"The Pleko web app."

import flask

import pleko

app = flask.Flask(__name__)

@app.route('/')
def home():
    return flask.render_template('base.html')

@app.route('/user/<name>')
def user(name):
    return "<h1>Hello {}!</h1>".format(name)

@app.route('/version')
def version():
    return "<h1>Version {}</h1>".format(pleko.__version__)


if __name__ == '__main__':
    app.run(debug=True)
