"Documentation HTML endpoints."

import http.client
import os
import os.path

import flask
import yaml

from dbshare import constants


DOCUMENTATION = {}


blueprint = flask.Blueprint("documentation", __name__)


@blueprint.route("/endpoints")
def endpoints():
    "Display all URL endpoints."
    endpoints = {}
    trivial_methods = set(["HEAD", "OPTIONS"])
    for rule in flask.current_app.url_map.iter_rules():
        endpoints[rule.endpoint] = {
            "url": rule.rule,
            "methods": sorted(rule.methods.difference(trivial_methods)),
        }
    for name, func in flask.current_app.view_functions.items():
        endpoints[name]["doc"] = func.__doc__
    endpoints["static"]["doc"] = "Static web page support files."
    urls = sorted([(e["url"], e) for e in endpoints.values()])
    return flask.render_template("url_endpoints.html", urls=urls)


@blueprint.route("/")
def home():
    "Home documentation page in Markdown format."
    try:
        doc = DOCUMENTATION["overview"]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.render_template(
        "documentation.html", doc=doc, docs=DOCUMENTATION.values()
    )


@blueprint.route("/<page>")
def page(page):
    "Documentation page in Markdown format."
    try:
        doc = DOCUMENTATION[page]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.render_template(
        "documentation.html", doc=doc, docs=DOCUMENTATION.values()
    )


def init(app):
    "Initialize; read the documentation files."
    docs = []
    for filename in os.listdir(app.config["DOCUMENTATION_DIR"]):
        if not filename.endswith(".md"):
            continue
        docs.append(Documentation(app.config["DOCUMENTATION_DIR"], filename))
    docs.sort(key=lambda d: d.ordinal)
    DOCUMENTATION.update(dict([(d.slug, d) for d in docs]))


class Documentation:
    "Documentation text; front matter and Markdown text."

    def __init__(self, dirpath, filename):
        with open(os.path.join(dirpath, filename)) as infile:
            data = infile.read()
        match = constants.FRONT_MATTER_RX.match(data)
        if match:
            try:
                self.front_matter = yaml.safe_load(match.group(1)) or {}
            except yaml.parser.ParserError:
                raise IOError(f"Invalid YAML in {abspath}")
            self.md = data[match.end() :]
        else:
            self.front_matter = {}
            self.md = data
        self.slug = os.path.splitext(filename)[0]
        try:
            self.title = self.front_matter["title"]
        except KeyError:
            self.title = self.slug.capitalize()
        try:
            self.level = int(self.front_matter["level"])
        except (KeyError, ValueError):
            self.level = 0
        try:
            self.ordinal = self.front_matter["ordinal"]
        except KeyError:
            self.ordinal = 1000000
