import unittest
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


if __name__ == '__main__':
    unittest.main()
