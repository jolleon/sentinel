import unittest
from sentinel import *

class TestValidateValid(unittest.TestCase):

    def test_integer(self):
        validate(0, 0)
        validate(1, 1)
        validate(0, 1)
        validate(1, 2)
        validate(-30, 2)

    def test_string(self):
        validate('', '')
        validate('a', 'a')
        validate('a', 'b')
        validate('a', 'dhajkl')

    def test_list(self):
        validate([], [])
        validate([1], [213])

    def test_dict(self):
        validate({}, {})
        validate({1: 1}, {1: 2})
        validate(
            {'aa': 1, 2: 'asd'},
            {'aa': 4, 2: 'jdksla'}
        )

    def test_none(self):
        validate(None, None)


class TestValidateInvalid(unittest.TestCase):

    invalids = [
        1,
        None,
        'asd',
        [],
        [1],
        ['asd'],
        [1, 2],
        [1, 'as'],
        {},
        {1: 3},
        {1: 'a'},
        {2: 2},
        {1: 2, 2: 3},
    ]

    def test_invalids(self):
        for a in self.invalids:
            for b in self.invalids:
                if a is not b:
                    self.assertRaises(AssertionError, validate, a, b)



if __name__ == '__main__':
    unittest.main()
