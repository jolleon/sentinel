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

    def _test_wrongs(self, exc, wrongs):
        for a in wrongs:
            for b in wrongs:
                if a is not b:
                    self.assertRaises(exc, validate, a, b)

    def test_wrong_type(self):
        invalid_types = [
            1,
            None,
            'asd',
            [1],
            ['a'],
            [None],
            {1: 'b'},
        ]
        self._test_wrongs(WrongType, invalid_types)

    def test_wrong_length(self):
        wrong_lengths = [
            [],
            [1],
            [1, 2],
        ]
        self._test_wrongs(WrongLength, wrong_lengths)

    def test_wrong_keys(self):
        wrong_keys = [
            {},
            {1: 3},
            {2: 'a'},
            {1: 1, 2: 2},
        ]
        self._test_wrongs(WrongKeys, wrong_keys)


if __name__ == '__main__':
    unittest.main()
