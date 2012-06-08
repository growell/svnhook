#!/usr/bin/env python
######################################################################
# Test Commit List Filter
######################################################################
import os, re, sys, unittest
from subprocess import CalledProcessError

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

class TestFilterCommitList(HookTestCase):

    def setUp(self):
        super(TestFilterCommitList, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tags."""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <SendError>You're bothering me.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertNotEqual(
            p.returncode, 0,
            'Expected non-zero exit code missing.')

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Internal hook error',
            'Expected error message not found.')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-commit', r'xxx',
            'Expected error not found in hook log.')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterCommitList]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
