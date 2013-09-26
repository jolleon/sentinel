from string import Template


class Wrong(Exception):

    def __init__(self, path, schema, data):
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
