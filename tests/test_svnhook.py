#!/usr/bin/env python
import os, sys

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase
from svnhook.hooks import SvnHook

class TestSvnHook(HookTestCase):

    def setUp(self):
        super(TestSvnHook, self).setUp(__name__)

    def test_constructor(self):
        self.assertRaises(TypeError, SvnHook())

    def test_dummy(self):
        self.assertTrue(True)

if __name__=='__main__':
    unittest.main()
