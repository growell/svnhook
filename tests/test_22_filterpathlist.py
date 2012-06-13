#!/usr/bin/env python
######################################################################
# Test Path List Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

class TestFilterPathList(HookTestCase):
    """Path List Filter Tests"""

    def setUp(self):
        super(TestFilterPathList, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No path regex"""

        # Define the hook configuration.
        self.writeConf('post-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPathList>
              <SendError>Invalid path name.</SendError>
            </FilterPathList>
          </Actions>
          ''')

        # Lock a path.
        p = self.lockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'post-lock', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_match(self):
        """Path match"""

        # Define the hook configuration.
        self.writeConf('post-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPathList>
              <PathRegex>(?i)^/FILE</PathRegex>
              <SendError>Invalid path name.</SendError>
            </FilterPathList>
          </Actions>
          ''')

        # Apply the new lock.
        p = self.lockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'Invalid path name',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_03_mismatch(self):
        """Path mismatch"""

        # Define the hook configuration.
        self.writeConf('post-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPathList>
              <PathRegex>^/File</PathRegex>
              <SendError>Invalid path name.</SendError>
            </FilterPathList>
          </Actions>
          ''')

        # Apply the new lock.
        p = self.lockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that an error message wasn't produced.
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

        # Verify that an error wasn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterPathList]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
