#!/usr/bin/env python
######################################################################
# Test Path Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterPath(HookTestCase):
    """Path Filter Tests"""

    def setUp(self):
        super(TestFilterPath, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex_tag(self):
        """Path regex missing."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPath>
              <SendError>Path not allowed.</SendError>
            </FilterPath>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, '', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertEqual(
            p.returncode, 255,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_02_match(self):
        """Path true match."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPath>
              <PathRegex>A1</PathRegex>
              <SendError>Path not allowed.</SendError>
            </FilterPath>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA1.txt',
            self.username, 'All mine.', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Path not allowed',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_03_mismatch(self):
        """Path false mismatch."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterPath>
              <PathRegex sense="false">A1</PathRegex>
              <SendError>Path not allowed.</SendError>
            </FilterPath>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA1.txt',
            self.username, 'All mine.', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify that no error message is returned.
        self.assertNotRegexpMatches(
            stderrdata, r'/S',
            'Unexpected error message found')

        # Verify an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterPath]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
