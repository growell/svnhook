#!/usr/bin/env python
######################################################################
# Test Change Type Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterChgType(HookTestCase):
    """Change Type Filter Tests"""

    def setUp(self):
        super(TestFilterChgType, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_missing_regex(self):
        """Required regex tag missing."""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterChgType>
              <SendError>Change type not allowed.</SendError>
            </FilterChgType>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-revprop-change', self.repopath, 1,
            self.username, 'my:property', 'A')
        (stdoutdata, stderrdata) = p.communicate(input='new value\n')
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify an internal error is indicated.
        self.assertEquals(
            p.returncode & 0x7f, 0x7f,
            'Error exit code not found: exit code = {0}'\
                .format(p.returncode))

    def test_02_simple_regex_match(self):
        """Simple regex match."""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterChgType>
              <ChgTypeRegex>A</ChgTypeRegex>
              <SendError>Change type not allowed.</SendError>
            </FilterChgType>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-revprop-change', self.repopath, 1,
            self.username, 'my:property', 'A')
        (stdoutdata, stderrdata) = p.communicate(input='new value\n')
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Change type not allowed',
            'Expected error message not found')

        # Verify the normal error is indicated.
        self.assertEquals(
            p.returncode, 1,
            'Expected exit code not found')

    def test_03_mismatch(self):
        """Change type doesn't match."""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterChgType>
              <ChgTypeRegex>[MD]</ChgTypeRegex>
              <SendError>
                Revision properties cannot be altered.
              </SendError>
            </FilterChgType>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-revprop-change', self.repopath, 1,
            self.username, 'my:property', 'A')
        (stdoutdata, stderrdata) = p.communicate(input='new value\n')
        p.wait()

        # Verify an error isn't indicated.
        self.assertEquals(
            p.returncode, 0,
            'Expected exit code not found')

        # Verify no error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'(?s)^\s*$',
            'Unexpected error message found')

    def test_04_negative_match(self):
        """Negative regex match."""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterChgType sense="0">
              <ChgTypeRegex>A</ChgTypeRegex>
              <SendError>
                Revision properties cannot be altered.
              </SendError>
            </FilterChgType>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-revprop-change', self.repopath, 1,
            self.username, 'my:property', 'M')
        (stdoutdata, stderrdata) = p.communicate(input='new value\n')
        p.wait()

        # Verify an error isn't indicated.
        self.assertEquals(
            p.returncode, 0,
            'Expected exit code not found')

        # Verify no error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'(?s)^\s*$',
            'Unexpected error message found')

    def test_05_negative_mismatch(self):
        """Negative regex mismatch."""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterChgType sense="0">
              <ChgTypeRegex>A</ChgTypeRegex>
              <SendError>
                Revision properties cannot be altered.
              </SendError>
            </FilterChgType>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-revprop-change', self.repopath, 1,
            self.username, 'my:property', 'A')
        (stdoutdata, stderrdata) = p.communicate(input='new value\n')
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'cannot be altered',
            'Expected error message not found')

        # Verify the normal error is indicated.
        self.assertEquals(
            p.returncode, 1,
            'Expected exit code not found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterChgType]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
