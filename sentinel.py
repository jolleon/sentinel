def validate(schema, data):
    assert type(schema) is type(data)
    if type(schema) is list:
        assert len(schema) == len(data)
        for (schema_item, item) in zip(schema, data):
            validate(schema_item, item)
    if type(schema) is dict:
        assert sorted(schema.keys()) == sorted(data.keys())
        for key in schema.keys():
            validate(schema[key], data[key])
