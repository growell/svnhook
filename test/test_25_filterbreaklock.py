#!/usr/bin/env python
######################################################################
# Test Steal Lock Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterStealLock(HookTestCase):
    """Steal Lock Filter Tests"""

    def setUp(self):
        super(TestFilterStealLock, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_default_match(self):
        """Default sense with set flag."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterStealLock>
              <SendError>Cannot steal other user's lock!</SendError>
            </FilterStealLock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA1.txt',
            self.username, 'mytoken', 1)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Cannot steal other user',
            'Expected error message not found')

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found: '\
            ' exit code = {}'.format(p.returncode))

    def test_02_default_mismatch(self):
        """Default sense with unset flag."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterStealLock>
              <SendError>Cannot steal other user's lock!</SendError>
            </FilterStealLock>
          </Actions>
          ''')

        # Call the script with the flag unset.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA1.txt',
            self.username, 'mytoken', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found: '\
            ' exit code = {}'.format(p.returncode))

        # Verify an error message isn't returned.
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

    def test_03_explicit_match(self):
        """Explicit sense with matching set flag."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterStealLock sense="true">
              <SendError>Cannot steal other user's lock!</SendError>
            </FilterStealLock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA2.txt',
            self.username, 'mytoken', 1)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Cannot steal other user',
            'Expected error message not found')

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found: '\
            ' exit code = {}'.format(p.returncode))

    def test_04_explicit_match2(self):
        """Explicit sense with matching unset flag."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterStealLock sense="false">
              <SendError>Cannot get new locks?!</SendError>
            </FilterStealLock>
          </Actions>
          ''')

        # Call the script with the flag unset.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA2.txt',
            self.username, 'mytoken', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Cannot get new locks',
            'Expected error message not found')

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found: '\
            ' exit code = {}'.format(p.returncode))

    def test_05_explicit_mismatch(self):
        """Explicit sense with mismatched set flag."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterStealLock sense="false">
              <SendError>Cannot get new locks?!</SendError>
            </FilterStealLock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-lock', self.repopath, '/fileA2.txt',
            self.username, 'mytoken', 1)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the exit code is correct.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found: '\
            ' exit code = {}'.format(p.returncode))

        # Verify an error message isn't returned.
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterStealLock]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
