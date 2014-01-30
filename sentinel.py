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


class Type(object):
    pass


class ValueType(Type):

    def __init__(self, value):
        self.value = value

    def validate(self, data):
        problems = []
        if type(data) is not type(self.value):
            problems.append(InvalidTypeProblem(type(self.value), type(data)))
        return problems


def config(**defaults):
    options = ['validators'] + defaults.keys()

    class Config(namedtuple('Config', options)):
        def __new__(cls, validators=None, **kw):
            kwargs = {}
            kwargs.update(defaults)
            kwargs.update(kw)
            if validators is None:
                validators = []
            return super(Config, cls).__new__(cls, validators, **kwargs)

    return Config

Config = config()

ListConfig = config(min_length=None, max_length=None)

class DictConfig(config(unexpected='raise')):
    def __new__(cls, **kw):
        conf = super(DictConfig, cls).__new__(cls, **kw)
        assert conf.unexpected in ['raise', 'ignore']
        return conf


class ListType(Type):

    def __init__(self, child_schema, config=None):
        self.child_schema = child_schema
        if config is None:
            config = ListConfig()
        self.config = config

    @classmethod
    def build(cls, data):
        if type(data) is ListType:
            return data
        assert type(data) is list
        # model should contain only 1 item and optionally a config
        assert len(data) == 1 or (len(data) == 2 and isinstance(data[1], ListConfig))
        child_schema = build_schema(data[0])
        if len(data) == 2:
            config = data[1]
        else:
            config = ListConfig()
        return cls(child_schema, config)

    def validate(self, data):
        problems = []
        if self.config.min_length is not None and len(data) < self.config.min_length:
            problems.append(
                Problem(
                    'List is too short',
                    'min=%d, actual=%d' % (self.config.min_length, len(data))
                )
            )
        if self.config.max_length is not None and len(data) > self.config.max_length:
            problems.append(
                Problem(
                    'List is too long',
                    'max=%d, actual=%d' % (self.config.max_length, len(data))
                )
            )
        for i, child in enumerate(data):
            child_problems = self.child_schema.validate(child)
            for p in child_problems:
                p.add_path(i)
                problems.append(p)
        return problems


config_key = 'sentinelconfignooneusethatihope'

class DictType(Type):

    def __init__(self, mapping, config=None):
        self.mapping = mapping
        if config is None:
            config = DictConfig()
        self.config = config

    @classmethod
    def build(cls, model):
        if type(model) is DictType:
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
    if type(data) is dict:
        return DictType.build(data)
    return ValueType(data)
