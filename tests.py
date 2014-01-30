import unittest
from mock import Mock
from mock import patch

from sentinel import *


class TestSchema(unittest.TestCase):

    def test_serialize_invalid(self):
        schema = Schema()
        schema.validate = Mock()
        schema.validate.return_value = [Mock()]
        self.assertRaises(Invalid, schema.serialize, Mock())

    def test_serialize_valid(self):
        schema = Schema()
        schema.validate = Mock()
        schema.validate.return_value = []
        data = Mock()
        self.assertEqual(data, schema.serialize(data))


class TestValueSchema(unittest.TestCase):

    def _test_valid(self, value, data):
        schema = ValueSchema(value)
        problems = schema.validate(data)
        self.assertEqual(problems, [])

    def test_valid_int(self):
        self._test_valid(1, 2)
        self._test_valid(0, 123)
        self._test_valid(3, 3)

    def _test_invalid(self, value, data):
        schema = ValueSchema(value)
        problems = schema.validate(data)
        assert len(problems) > 0

    def test_invalid(self):
        self._test_invalid(1, 'sad')
        self._test_invalid('asd', None)


class TestListConfig(unittest.TestCase):

    def test_defaults(self):
        conf = ListConfig()
        self.assertEqual(conf.min_length, None)
        self.assertEqual(conf.max_length, None)


class TestListSchema(unittest.TestCase):

    def _test_with_config(self, config, data, problems):
        child_schema = Mock()
        child_schema.validate.return_value = []
        schema = ListSchema(child_schema, config)
        self.assertEqual(
            problems,
            schema.validate(data)
        )

    def test_min_length_invalid(self):
        config = ListConfig(min_length=2)
        data = [Mock()]
        problems = [Problem('List is too short', 'min=2, actual=1', '')]
        self._test_with_config(config, data, problems)

    def test_min_length_valid(self):
        config = ListConfig(min_length=2)
        self._test_with_config(config, [Mock(), Mock()], [])

    def test_max_length_invalid(self):
        config = ListConfig(max_length=2)
        data = [Mock(), Mock(), Mock()]
        problems = [Problem('List is too long', 'max=2, actual=3', '')]
        self._test_with_config(config, data, problems)

    def test_max_length_valid(self):
        config = ListConfig(max_length=2)
        self._test_with_config(config, [Mock(), Mock()], [])

    def test_max_length_valid_empty(self):
        config = ListConfig(max_length=2)
        self._test_with_config(config, [], [])

    def test_propagate(self):
        child_schema = Mock()
        child_schema.validate.return_value = [Problem('bla', 'bli', '')]
        schema = ListSchema(child_schema)
        self.assertEqual(
            [Problem('bla', 'bli', '0')],
            schema.validate([Mock()])
        )

    def test_propagate_multiple(self):
        child_schema = Mock()
        child_schema.validate.side_effect = [
            [Problem('bla0', 'bli', '')],
            [Problem('bla10', 'bli', ''), Problem('bla11', 'bli', '')]
        ]
        schema = ListSchema(child_schema)
        self.assertEqual([
                Problem('bla0', 'bli', '0'),
                Problem('bla10', 'bli', '1'),
                Problem('bla11', 'bli', '1')
            ],
            schema.validate([Mock(), Mock()])
        )


class IntegrationTestListSchema(unittest.TestCase):

    def test_build_schema_no_config(self):
        schema = ListSchema.build_schema([1])
        # created child schema
        self.assertEqual(ValueSchema, type(schema.child_schema))
        # default config
        self.assertEqual(ListConfig(), schema.config)

    def test_build_schema_with_config(self):
        config = ListConfig(min_length=5)
        schema = ListSchema.build_schema([2, config])
        self.assertEqual(ValueSchema, type(schema.child_schema))
        self.assertEqual(config, schema.config)

    def test_build_schema_invalid(self):
        config = ListConfig(min_length=5)
        self.assertRaises(
            AssertionError,
            ListSchema.build_schema,
            [config, 3]
        )
        self.assertRaises(
            AssertionError,
            ListSchema.build_schema,
            [2, 3]
        )
        self.assertRaises(
            AssertionError,
            ListSchema.build_schema,
            []
        )


class TestDictConfig(unittest.TestCase):

    def test_defaults(self):
        conf = DictConfig()
        self.assertEqual(conf.unexpected, 'raise')

    def test_invalid_unexpected(self):
        self.assertRaises(
            AssertionError,
            DictConfig,
            unexpected='not an option'
        )


class IntegrationTestDictConfig(unittest.TestCase):

    def setUp(self):
        self.model = {
            config_key: DictConfig(),
            1: 1,
            'a': 3,
            'my_object': {}
        }

    def test_find_config(self):
        schema = build_schema(self.model)
        self.assertEqual(schema.config, self.model[config_key])


class IntegrationTestDictSchema(unittest.TestCase):

    def setUp(self):
        self.model = {
            1: 1,
            'a': 3,
            'my_object': {}
        }
        self.data = self.model.copy() #TODO: deepcopy?
        self.schema = build_schema(self.model)

    def test_valid_self(self):
        problems = self.schema.validate(self.model)
        self.assertEqual(problems, [])

    def test_valid(self):
        self.data[1] = 2
        self.data['a'] = 54
        problems = self.schema.validate(self.data)
        self.assertEqual(problems, [])

    def test_unexpected_raise(self):
        self.model[config_key] = DictConfig(unexpected='raise')
        schema = build_schema(self.model)
        self.data['new_key'] = 'a'
        problems = schema.validate(self.data)
        self.assertEqual(problems, [
            Problem('Unexpected Key','new_key', path='')
        ])

    def test_unexpected_ignore(self):
        self.model[config_key] = DictConfig(unexpected='ignore')
        schema = build_schema(self.model)
        self.data['new_key'] = 'a'
        problems = schema.validate(self.data)
        self.assertEqual(problems, [])

    def test_propagate(self):
        self.data[1] = 'a'
        problems = self.schema.validate(self.data)
        self.assertEqual(problems, [
            InvalidTypeProblem(int, str, path='1')
        ])

    def test_propagate_2(self):
        self.data[1] = 'a'
        self.data['a'] = 'a'
        problems = self.schema.validate(self.data)
        self.assertEqual(problems, [
            InvalidTypeProblem(int, str, path='a'),
            InvalidTypeProblem(int, str, path='1'),
        ])

    def test_missing_key_value(self):
        del self.data['a']
        problems = self.schema.validate(self.data)
        self.assertEqual(problems, [
            Problem('Missing Key', 'a', '')
        ])

    def test_missing_key_dict(self):
        del self.data['my_object']
        problems = self.schema.validate(self.data)
        self.assertEqual(problems, [
            Problem('Missing Key', 'my_object', '')
        ])


if __name__ == '__main__':
    unittest.main()
