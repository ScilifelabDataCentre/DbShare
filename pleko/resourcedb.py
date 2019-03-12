"Base abstract ResourceDb class; resource database."


class BaseResourceDb:
    "Base abstract ResourceDb class."

    def __init__(self, config):
        "Connect to the database."
        raise NotImplementedError

    def initialize(self):
        "Initialize the database."
        pass
    def __iter__(self):
        "Return an iterator over all resources."
        raise NotImplementedError

    def __getitem__(self, identifier):
        """Get the resource by identifier.
        Raise KeyError if no such resource.
        """
        raise NotImplementedError

    def get(self, identifier, default=None):
        "Get the user by identifier; default if none."
        try:
            return self[identifier]
        except KeyError:
            return default
