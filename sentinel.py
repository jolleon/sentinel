from collections import namedtuple
from string import Template

class Invalid(Exception):
    pass


class SchemaError(Exception):
    pass


class Problem(object):
    def __init__(self, error, reason, path=''):
        self.error = error
        self.reason = reason
        self.path = path

    def add_path(self, node):
        if self.path != '':
            self.path = str(node) + '.' + self.path
        else:
            self.path = str(node)

    def __eq__(self, other):
        return self.error == other.error and self.reason == other.reason and self.path == other.path

    def __repr__(self):
        return "{path}: {error}: {reason}".format(
            path=self.path,
            error=self.error,
            reason=self.reason,
        )


class InvalidTypeProblem(Problem):
    error = 'Invalid Type'
    reason = 'expected={expected}, actual={actual}'

    def __init__(self, expected, actual, **kwargs):
        reason = self.reason.format(expected=expected, actual=actual)
        super(InvalidTypeProblem, self).__init__(self.error, reason, **kwargs)


class Schema(object):

    def serialize(self, data):
        problems = self.validate(data)
        if len(problems) > 0:
            raise Invalid(problems)
        return data

    def deserialize(self, data):
        return self.serialize(data)


class ValueSchema(Schema):

    def __init__(self, value):
        self.value = value

    def validate(self, data):
        problems = []
        if type(data) is not type(self.value):
            problems.append(InvalidTypeProblem(type(self.value), type(data)))
        return problems


class TupleSchema(Schema):

    def __init__(self, children):
        self.children = children

    @classmethod
    def build_schema(cls, data):
        if type(data) is TupleSchema:
            return data
        assert type(data) is tuple
        children = []
        for item in data:
            item_schema = build_schema(item)
            children.append(item_schema)
        return cls(children)

    def validate(self, data):
        problems = []
        if len(data) != len(self.children):
            problems.append(
                Problem(
                    'Different Lengths',
                    'expected=%d, actual=%d' % (len(self.children), len(data))
                )
            )
        for i, (child, data_child) in enumerate(zip(self.children, data)):
            child_problems = child.validate(data_child)
            for p in child_problems:
                p.add_path(i)
                problems.append(p)
        return problems


class DictConfig(namedtuple('DictConfig', [
    'unexpected',
    ])):
    def __new__(cls, unexpected='raise'):
        assert unexpected in ['raise', 'ignore']
        return super(DictConfig, cls).__new__(cls, unexpected)


config_key = 'sentinelconfignooneusethatihope'

class DictSchema(Schema):

    def __init__(self, mapping, config=None):
        self.mapping = mapping
        if config is None:
            config = DictConfig()
        self.config = config

    @classmethod
    def build_schema(cls, model):
        if type(model) is DictSchema:
            return model

        assert type(model) is dict
        config = None
        mapping = {}
        for key, value in model.iteritems():
            if key == config_key:
                assert isinstance(value, DictConfig)
                config = value
            else:
                mapping[key] = build_schema(value)
        return cls(mapping, config=config)

    def validate(self, data):
        problems = []
        for key in self.mapping:
            if key not in data:
                problems.append(
                    Problem('Missing Key', str(key))
                )
            else:
                child_problems = self.mapping[key].validate(data[key])
                for p in child_problems:
                    p.add_path(key)
                    problems.append(p)
        if self.config.unexpected == 'raise':
            for key in data:
                if key not in self.mapping:
                    problems.append(
                        Problem('Unexpected Key', str(key))
                    )
        return problems



def build_schema(data):
    if isinstance(data, Schema):
        return data
    if type(data) is tuple:
        return TupleSchema.build_schema(data)
    if type(data) is dict:
        return DictSchema.build_schema(data)
    return ValueSchema(data)
