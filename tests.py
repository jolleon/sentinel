import unittest
import mock
from mock import Mock

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


class TestListSchema(unittest.TestCase):

    def test_validate_valid(self):
        children = [Mock(), Mock()]
        schema = ListSchema(children)
        data = [Mock(), Mock()]

        children[0].validate.return_value = []
        children[1].validate.return_value = []

        problems = schema.validate(data)

        self.assertEqual(problems, [])
        children[0].validate.assert_called_once_with(data[0])
        children[1].validate.assert_called_once_with(data[1])

    def test_validate_propagates(self):
        children = [Mock(), Mock()]
        schema = ListSchema(children)
        data = [Mock(), Mock()]

        children[0].validate.return_value = []
        child1_problems = [Mock(), Mock()]
        children[1].validate.return_value = child1_problems

        problems = schema.validate(data)

        self.assertEqual(problems, child1_problems)
        children[0].validate.assert_called_once_with(data[0])
        children[1].validate.assert_called_once_with(data[1])
        child1_problems[0].add_path.assert_called_once_with(1)
        child1_problems[1].add_path.assert_called_once_with(1)



class IntegrationTestValidate(unittest.TestCase):

    def setUp(self):

        self.model = {
            1: 1,
            'asd': None,
            'my_list': [1, 2],
            'my_object': {
                'other_list': ['a'],
                2: 4,
                'other_object': {
                    2: 4
                },
                3: [
                    {
                        'a': 3
                    }
                ]
            }
        }

        self.schema = build_schema(self.model)

    def test_build_schema(self):
        self.assertEqual(type(self.schema), DictSchema)

    def test_valid(self):
        problems = self.schema.validate(self.model)
        self.assertEqual(problems, [])

        self.model[1] = 3
        problems = self.schema.validate(self.model)
        self.assertEqual(problems, [])

        self.model['my_list'][0] = 4
        problems = self.schema.validate(self.model)
        self.assertEqual(problems, [])

    def test_invalid_1(self):
        self.model[1] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Invalid Type', int, str, '1')
        ]))

    def test_invalid_2(self):
        self.model['asd'] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Invalid Type', type(None), str, 'asd')
        ]))

    def test_invalid_3(self):
        self.model['new_key'] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Unexpected Key', None, 'new_key', '')
        ]))

    def test_invalid_4(self):
        del self.model['asd']
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Missing Key', 'asd', None, '')
        ]))

    def test_invalid_5(self):
        del self.model['my_object']
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Missing Key', 'my_object', None, '')
        ]))

    def test_invalid_6(self):
        del self.model['my_list']
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Missing Key', 'my_list', None, '')
        ]))

    def test_invalid_7(self):
        self.model['my_object']['other_list'][0] = 2
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Invalid Type', str, int, 'my_object.other_list.0')
        ]))

    def test_invalid_8(self):
        self.model['my_object'][3][0]['a'] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Invalid Type', int, str, 'my_object.3.0.a')
        ]))

    def test_invalid_9(self):
        self.model['my_object'][3][0]['b'] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Unexpected Key', None, 'b', 'my_object.3.0')
        ]))

    def test_invalid_10(self):
        self.model['my_object'][3][0]['b'] = 'a'
        self.model['my_object'][3][0]['a'] = 'a'
        problems = self.schema.validate(self.model)
        self.assertEqual(repr(problems), repr([
            Problem('Invalid Type', int, str, 'my_object.3.0.a'),
            Problem('Unexpected Key', None, 'b', 'my_object.3.0')
        ]))

if __name__ == '__main__':
    unittest.main()
