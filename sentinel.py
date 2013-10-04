from string import Template

class Invalid(Exception):
    pass


class Schema(object):

    def serialize(self, data):
        problems = self.validate(data)
        if len(problems) > 0:
            raise Invalid(problems)
        return data

    def deserialize(self, data):
        return self.serialize(data)


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
        return "{path}: {reason} (expected={expected},  actual={actual})".format(
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
