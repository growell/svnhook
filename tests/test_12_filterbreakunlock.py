#!/usr/bin/env python
######################################################################
# Test Break Unlock Filter
######################################################################
import os, re, sys, unittest, time
from subprocess import CalledProcessError

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

class TestFilterBreakUnlock(HookTestCase):
    """Break Unlock Filter Tests"""

    def setUp(self):
        super(TestFilterBreakUnlock, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_default_match(self):
        """Default sense with set flag."""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterBreakUnlock>
              <SendError>Cannot remove other user's lock!</SendError>
            </FilterBreakUnlock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-unlock', self.repopath, '/file1.txt',
            self.username, 'mytoken', '1')

        # Verify the proper error message is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Cannot remove other user',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertTrue(
            p.returncode != 0,
            'Unexpected success exit code found')

    def test_02_default_mismatch(self):
        """Default sense with unset flag."""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterBreakUnlock>
              <SendError>Cannot remove other user's lock!</SendError>
            </FilterBreakUnlock>
          </Actions>
          ''')

        # Call the script with the flag unset.
        p = self.callHook(
            'pre-unlock', self.repopath, '/file1.txt',
            self.username, 'mytoken', '0')

        # Verify a failure isn't indicated.
        self.assertTrue(
            p.returncode == 0,
            'Expected success exit code not found')

        # Verify an error message isn't returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

    def test_03_explicit_match(self):
        """Explicit sense with matching set flag."""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterBreakUnlock sense="true">
              <SendError>Cannot remove other user's lock!</SendError>
            </FilterBreakUnlock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-unlock', self.repopath, '/file2.txt',
            self.username, 'mytoken', '1')

        # Verify the proper error message is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Cannot remove other user',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertTrue(
            p.returncode != 0,
            'Unexpected success exit code found')

    def test_04_explicit_match2(self):
        """Explicit sense with matching unset flag."""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterBreakUnlock sense="false">
              <SendError>Cannot remove your own lock?!</SendError>
            </FilterBreakUnlock>
          </Actions>
          ''')

        # Call the script with the flag unset.
        p = self.callHook(
            'pre-unlock', self.repopath, '/file2.txt',
            self.username, 'mytoken', '0')

        # Verify the proper error message is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Cannot remove your own',
            'Expected error message not found')

        # Verify a failure isn't indicated.
        self.assertTrue(
            p.returncode != 0,
            'Unexpected success exit code found')

    def test_05_explicit_mismatch(self):
        """Explicit sense with mismatched set flag."""

        # Define the hook configuration.
        self.writeConf('pre-unlock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterBreakUnlock sense="false">
              <SendError>Cannot remove your own lock?!</SendError>
            </FilterBreakUnlock>
          </Actions>
          ''')

        # Call the script with the flag set.
        p = self.callHook(
            'pre-unlock', self.repopath, '/file2.txt',
            self.username, 'mytoken', '1')

        # Verify a failure isn't indicated.
        self.assertTrue(
            p.returncode == 0,
            'Unexpected error exit code found')

        # Verify an error message isn't returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterBreakUnlock]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
