import unittest
import util

class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.widget = 'The widget'

    def tearDown(self):
        #self.widget.dispose()
        self.widget = None

    def test_empty_string(self):
        answer = util.elideString("")
        self.assertEqual(answer,"***")

    def test_string_of_9(self):
        answer = util.elideString("123456789")
        self.assertEqual(answer,"123...789")
        
    def test_string_of_12(self):
        answer = util.elideString("12345678901")
        self.assertEqual(answer,"123...901")
        
    def test_string_of_5(self):
        answer = util.elideString("12345")
        self.assertEqual(answer,"***")

    def test_darn_long_string(self):
        answer = util.elideString("Return version of string with the middle removed.  This allows identifying")
        self.assertEqual(answer,"Ret...ing")
