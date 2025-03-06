from server.db import crud
import unittest


class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def testSelectTradepairs(self):
        all_tradepairs = crud.selectTradepairs()
        
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)
    def testSelectCandles():
        pass
    def testSwitchTradepairStatus():
        pass
    def testAddTradepairs():
        pass
    def testAddCandles():
        pass

if __name__ == '__main__':
    unittest.main()