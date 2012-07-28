#!/usr/bin/env python
######################################################################
# Test Lock Token Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterLockToken(HookTestCase):
    """Lock Token Filter Tests"""

    def setUp(self):
        super(TestFilterLockToken, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No lock token regex"""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockToken>
              <SendError>Invalid lock token.</SendError>
            </FilterLockToken>
          </Actions>
          ''')

        # Apply a new lock to an unlocked path.
        p = self.lockWcPath('fileA1.txt')
        self.assertEqual(
            p.returncode, 0,
            'Lock success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Unlock the path.
        p = self.unlockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-unlock', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_match(self):
        """Lock token match"""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockToken>
              <LockTokenRegex>opaque.+</LockTokenRegex>
              <SendError>Invalid lock token.</SendError>
            </FilterLockToken>
          </Actions>
          ''')

        # Apply a new lock to an unlocked path.
        p = self.lockWcPath('fileA1.txt')
        self.assertEqual(
            p.returncode, 0,
            'Lock success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Unlock the path.
        p = self.unlockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'Invalid lock token',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

    def test_03_mismatch(self):
        """Lock token mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockToken>
              <LockTokenRegex>zopaque.+</LockTokenRegex>
              <SendError>Invalid lock token.</SendError>
            </FilterLockToken>
          </Actions>
          ''')

        # Apply a new lock to an unlocked path.
        p = self.lockWcPath('fileA1.txt')
        self.assertEqual(
            p.returncode, 0,
            'Lock success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Unlock the path.
        p = self.unlockWcPath('fileA1.txt')
        stdoutdata, stderrdata = p.communicate()

        # Verify that an error message wasn't produced.
<<<<<<< HEAD
        self.assertRegexpMatches(
            stderrdata, r'(?s)^\s*$',
=======
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
>>>>>>> origin/master
            'Unexpected error message found')

        # Verify that an error wasn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterLockToken]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
