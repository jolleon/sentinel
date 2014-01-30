import unittest
from mock import Mock
from mock import patch

from sentinel import *


class TestSchema(unittest.TestCase):

    def test_serialize_invalid(self):
        mock_type = Mock()
        mock_data = Mock()
        schema = Schema(mock_type)
        mock_type.validate.return_value = [Mock()]
        self.assertRaises(Invalid, schema.validate, mock_data)
        mock_type.validate.assert_called_once_with(mock_data)

    def test_serialize_valid(self):
        mock_type = Mock()
        mock_data = Mock()
        schema = Schema(mock_type)
        mock_type.validate.return_value = []
        self.assertEqual(mock_data, schema.validate(mock_data))
        mock_type.validate.assert_called_once_with(mock_data)


class IntegrationTestSchema(unittest.TestCase):

    def test_build_schema(self):
        data = {'a': 1}
        schema = build_schema(data)
        self.assertEqual(Schema, type(schema))
        self.assertEqual(DictNode, type(schema.node))


class TestValueNode(unittest.TestCase):

    def _test_valid(self, value, data):
        node = ValueNode.build(value)
        problems = node.validate(data)
        self.assertEqual(problems, [])

    def test_valid_int(self):
        self._test_valid(1, 2)
        self._test_valid(0, 123)
        self._test_valid(3, 3)

    def _test_invalid(self, value, data):
        node = ValueNode.build(value)
        problems = node.validate(data)
        assert len(problems) > 0

    def test_invalid(self):
        self._test_invalid(1, 'sad')
        self._test_invalid('asd', None)


class TestListConfig(unittest.TestCase):

    def test_defaults(self):
        conf = ListConfig()
        self.assertEqual(conf.min_length, None)
        self.assertEqual(conf.max_length, None)


class TestListNode(unittest.TestCase):

    def _test_with_config(self, config, data, problems):
        child_node = Mock()
        child_node.validate.return_value = []
        node = ListNode(child_node, config)
        self.assertEqual(
            problems,
            node.validate(data)
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
        child_node = Mock()
        child_node.validate.return_value = [Problem('bla', 'bli', '')]
        node = ListNode(child_node)
        self.assertEqual(
            [Problem('bla', 'bli', '0')],
            node.validate([Mock()])
        )

    def test_propagate_multiple(self):
        child_node = Mock()
        child_node.validate.side_effect = [
            [Problem('bla0', 'bli', '')],
            [Problem('bla10', 'bli', ''), Problem('bla11', 'bli', '')]
        ]
        node = ListNode(child_node)
        self.assertEqual([
                Problem('bla0', 'bli', '0'),
                Problem('bla10', 'bli', '1'),
                Problem('bla11', 'bli', '1')
            ],
            node.validate([Mock(), Mock()])
        )


class IntegrationTestListNode(unittest.TestCase):

    def test_build_no_config(self):
        node = ListNode.build([1])
        # created child node
        self.assertEqual(ValueNode, type(node.child_node))
        # default config
        self.assertEqual(ListConfig(), node.config)

    def test_build_with_config(self):
        config = ListConfig(min_length=5)
        node = ListNode.build([2, config])
        self.assertEqual(ValueNode, type(node.child_node))
        self.assertEqual(config, node.config)

    def test_build_invalid(self):
        config = ListConfig(min_length=5)
        self.assertRaises(
            AssertionError,
            ListNode.build,
            [config, 3]
        )
        self.assertRaises(
            AssertionError,
            ListNode.build,
            [2, 3]
        )
        self.assertRaises(
            AssertionError,
            ListNode.build,
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
        node = build_node(self.model)
        self.assertEqual(node.config, self.model[config_key])


class IntegrationTestDictNode(unittest.TestCase):

    def setUp(self):
        self.model = {
            1: 1,
            'a': 3,
            'my_object': {}
        }
        self.data = self.model.copy() #TODO: deepcopy?
        self.node = build_node(self.model)

    def test_valid_self(self):
        problems = self.node.validate(self.model)
        self.assertEqual(problems, [])

    def test_valid(self):
        self.data[1] = 2
        self.data['a'] = 54
        problems = self.node.validate(self.data)
        self.assertEqual(problems, [])

    def test_unexpected_raise(self):
        self.model[config_key] = DictConfig(unexpected='raise')
        node = build_node(self.model)
        self.data['new_key'] = 'a'
        problems = node.validate(self.data)
        self.assertEqual(problems, [
            Problem('Unexpected Key','new_key', path='')
        ])

    def test_unexpected_ignore(self):
        self.model[config_key] = DictConfig(unexpected='ignore')
        node = build_node(self.model)
        self.data['new_key'] = 'a'
        problems = node.validate(self.data)
        self.assertEqual(problems, [])

    def test_propagate(self):
        self.data[1] = 'a'
        problems = self.node.validate(self.data)
        self.assertEqual(problems, [
            InvalidTypeProblem(int, str, path='1')
        ])

    def test_propagate_2(self):
        self.data[1] = 'a'
        self.data['a'] = 'a'
        problems = self.node.validate(self.data)
        self.assertEqual(problems, [
            InvalidTypeProblem(int, str, path='a'),
            InvalidTypeProblem(int, str, path='1'),
        ])

    def test_missing_key_value(self):
        del self.data['a']
        problems = self.node.validate(self.data)
        self.assertEqual(problems, [
            Problem('Missing Key', 'a', '')
        ])

    def test_missing_key_dict(self):
        del self.data['my_object']
        problems = self.node.validate(self.data)
        self.assertEqual(problems, [
            Problem('Missing Key', 'my_object', '')
        ])


if __name__ == '__main__':
    unittest.main()
