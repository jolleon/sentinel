from string import Template


class Wrong(Exception):

    def __init__(self, reason, schema, data):
        msg_template = Template('Invalid $invalid for $path\n expected: $schema\n   actual: $data')
        message = msg_template.substitute(invalid=self.invalid, path=path, schema=schema, data=data)
        Exception.__init__(self, message)


class WrongType(Wrong):
    invalid = 'type'

    def __init__(self, path, schema, data):
        Wrong.__init__(self, path=path, schema=type(schema), data=type(data))


class WrongLength(Wrong):
    invalid = 'length'

    def __init__(self, path, schema, data):
        Wrong.__init__(self, path=path, schema=len(schema), data=len(data))


class WrongKeys(Wrong):
    invalid = 'keys'

    def __init__(self, path, schema, data):
        Wrong.__init__(self, path=path, schema=schema.keys(), data=data.keys())


def validate(schema, data, prefix='<root>'):
    if type(schema) is not type(data):
        raise WrongType(prefix, schema, data)

    if type(schema) is list:
        if len(schema) != len(data):
            raise WrongLength(prefix, schema, data)
        for (schema_item, item) in zip(schema, data):
            validate(schema_item, item, prefix=prefix + '.[]')

    if type(schema) is dict:
        if sorted(schema.keys()) != sorted(data.keys()):
            raise WrongKeys(prefix, schema, data)
        for key in schema.keys():
            validate(schema[key], data[key], prefix=prefix + '.' + str(key))


class Schema(object):

    def __init__(self, schema):
        self.schema = schema

    def serialize(self, data):
        validate(self.schema, data)
        return data

    def deserialize(self, data):
        validate(self.schema, data)
        return data


class Problem(object):
    def __init__(self, reason, expected, actual):
        self.reason = reason
        self.expected = expected
        self.actual = actual
        self.path = ''

    def add_path(self, node):
        if self.path != '':
            self.path = str(node) + '.' + self.path
        else:
            self.path = str(node)

    def __repr__(self):
        return "{path}: {reason}\n expected: {expected}\n   actual: {actual}".format(
            path=self.path,
            reason=self.reason,
            expected=self.expected,
            actual=self.actual
        )

class ListSchema(Schema):

    def __init__(self, children):
        self.children = children

    @classmethod
    def build_schema(cls, data):
        if type(data) is ListSchema:
            return data
        assert type(data) is list
        children = []
        for item in data:
            item_schema = build_schema(item)
            children.append(item_schema)
        return cls(children)

    def validate(self, data):
        problems = []
        if len(data) != len(self.children):
            problems.append(
                Problem('Different Lengths', len(self.children), len(data))
            )
        for i, (child, data_child) in enumerate(zip(self.children, data)):
            child_problems = child.validate(data_child)
            for p in child_problems:
                p.add_path(i)
                problems.append(p)
        return problems

class DictSchema(Schema):

    def __init__(self, mapping):
        self.mapping = mapping

    @classmethod
    def build_schema(cls, data):
        if type(data) is DictSchema:
            return data
        assert type(data) is dict
        mapping = {}
        for key, value in data.iteritems():
            mapping[key] = build_schema(value)
        return cls(mapping)

    def validate(self, data):
        problems = []
        for key in self.mapping:
            if key not in data:
                problems.append(
                    #TODO: Missing None key would show weird
                    Problem('Missing Key', key, None)
                )
            else:
                child_problems = self.mapping[key].validate(data[key])
                for p in child_problems:
                    p.add_path(key)
                    problems.append(p)
        for key in data:
            if key not in self.mapping:
                problems.append(
                    Problem('Unexpected Key', None, key)
                )
        return problems



class ValueSchema(Schema):

    def __init__(self, value):
        self.value = value

    def validate(self, data):
        problems = []
        if type(data) is not type(self.value):
            problems.append(Problem('Invalid Type', type(self.value), type(data)))
        return problems



def build_schema(data):
    if isinstance(data, Schema):
        return data
    if type(data) is list:
        return ListSchema.build_schema(data)
    if type(data) is dict:
        return DictSchema.build_schema(data)
    return ValueSchema(data)
