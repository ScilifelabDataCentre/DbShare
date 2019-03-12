"Resource blueprint; type of resource determines features."

import importlib

# Resource database interface module
resourcedb = None

def init_app(app):
    "Import the configured resource database implementation and initialize it."
    global resourcedb
    resourcedb = importlib.import_module(app.config['RESOURCEDB_MODULE'])
    resourcedb.ResourceDb(app.config).initialize()
