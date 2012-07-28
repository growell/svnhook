#!/usr/bin/env python
######################################################################
# Test Lock Owner Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterLockOwner(HookTestCase):
    """Lock Owner Filter Tests"""

    def setUp(self):
        super(TestFilterLockOwner, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_owner(self):
        """No previous owner"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockOwner>
              <SendError>You are the lock owner.</SendError>
            </FilterLockOwner>
          </Actions>
          ''')

        # Apply a new lock to an unlocked path.
        p = self.lockWcPath('fileA1.txt', 'userA')
        stdoutdata, stderrdata = p.communicate()

        # Verify that no error message was produced.
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

        # Verify that an error wasn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_02_true_match(self):
        """Positive owner match"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockOwner>
              <SendError>You are the lock owner.</SendError>
            </FilterLockOwner>
          </Actions>
          ''')

        # Apply the original lock. Verify that an error wasn't
        # indicated.
        p = self.lockWcPath('fileA1.txt', 'userA')
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Apply another lock to the same path as the same user.
        p = self.lockWcPath('fileA1.txt', 'userA')
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'You are the lock owner',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_03_true_mismatch(self):
        """Positive owner mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockOwner>
              <SendError>You are the lock owner.</SendError>
            </FilterLockOwner>
          </Actions>
          ''')

        # Apply the original lock. Verify that an error wasn't
        # indicated.
        p = self.lockWcPath('fileA1.txt', 'userA')
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Force a lock on the same path as a different user. If we
        # don't force it, it'll skip the hook and fail with a warning.
        p = self.lockWcPath('fileA1.txt', 'userB', force=True)
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message wasn't produced.
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

        # Verify that an error wasn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_04_false_match(self):
        """Negative owner match"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockOwner sense="false">
              <SendError>You are not the lock owner.</SendError>
            </FilterLockOwner>
          </Actions>
          ''')

        # Apply the original lock. Verify that an error wasn't
        # indicated.
        p = self.lockWcPath('fileA1.txt', 'userA')
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Force a lock on the same path as a different user.
        p = self.lockWcPath('fileA1.txt', 'userB', force=True)
        stdoutdata, stderrdata = p.communicate()

        # Verify that the error message was produced.
        self.assertRegexpMatches(
            stderrdata, r'You are not the lock owner',
            'Expected error message not found')

        # Verify that an error was indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

    def test_05_false_mismatch(self):
        """Negative owner mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterLockOwner sense="false">
              <SendError>You are not the lock owner.</SendError>
            </FilterLockOwner>
          </Actions>
          ''')

        # Apply the original lock. Verify that an error wasn't
        # indicated.
        p = self.lockWcPath('fileA1.txt', 'userA')
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Force a lock on the same path as the same user.
        p = self.lockWcPath('fileA1.txt', 'userA', force=True)
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
    for tclass in [TestFilterLockOwner]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
