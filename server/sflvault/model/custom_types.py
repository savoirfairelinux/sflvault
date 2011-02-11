import simplejson

from sqlalchemy import types

class JSONEncodedDict(types.TypeDecorator):
    """Represents an mutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = types.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = simplejson.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        return simplejson.loads(value) if value else {}

    def copy_value(self, value):
        return simplejson.loads(simplejson.dumps(value))
