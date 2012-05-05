#!/usr/bin/env python
import os, sys
import unittest

class TestSvnHook(unittest.TestCase):

    def setUp(self):
        sys.path.insert(0, '..')
        import SvnHook

    def test_constructor(self):
        self.assertRaises(TypeError, SvnHook())

    def test_dummy(self):
        print 'Test it, you dummy!'
        self.assertTrue(True)

suite = unittest.TestLoader().loadTestsFromTestCase(TestSvnHook)
unittest.TextTestRunner(verbosity=2).run(suite)