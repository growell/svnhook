#!/usr/bin/env python
######################################################################
# Test Client Capabilities Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

# Test Hook and Configuration File
testhook = 'start-commit'
testconf = 'start-commit.xml'

class TestFilterCapabilities(HookTestCase):

    def setUp(self):
        super(TestFilterCapabilities, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_capabilities(self):
        """No client capabilities."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCapabilities>
              <CapabilitiesRegex sense="false">mergeinfo</CapabilitiesRegex>
              <SendError>Capability missing: mergeinfo</SendError>
            </FilterCapabilities>
          </Actions>
          ''')

        # Call the script with a mismatch.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Capability missing',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertTrue(p.returncode != 0,
                        'Expected error exit code is zero')

    def test_02_exact_match(self):
        """Exact capability match."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCapabilities>
              <CapabilitiesRegex sense="false">mergeinfo</CapabilitiesRegex>
              <SendError>Capability missing: mergeinfo</SendError>
            </FilterCapabilities>
          </Actions>
          ''')

        # Call the script with a single capability that exactly
        # matches the desired capability.
        p = self.callHook(testhook,
                          self.repopath, self.username, 'mergeinfo')

        # Verify that no error message is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

        # Verify that no failure is indicated.
        self.assertTrue(
            p.returncode == 0,
            'Expected success exit code is non-zero')

    def test_03_multiple_client_match(self):
        """Match capability in client list."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCapabilities>
              <CapabilitiesRegex sense="false">mergeinfo</CapabilitiesRegex>
              <SendError>Capability missing: mergeinfo</SendError>
            </FilterCapabilities>
          </Actions>
          ''')

        # Call the script with multiple colon-delimited capabilities
        # - one of which matches the desired capability.
        p = self.callHook(testhook,
                          self.repopath, self.username,
                          'mindread:mergeinfo:emote')

        # Verify that no error message is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
            'Unexpected error message found')

        # Verify that no failure is indicated.
        self.assertTrue(
            p.returncode == 0,
            'Expected success exit code is non-zero')

    def test_04_case_sensitive(self):
        """Case-sensitive client capabilities."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCapabilities>
              <CapabilitiesRegex sense="false">mergeinfo</CapabilitiesRegex>
              <SendError>Capability missing: mergeinfo</SendError>
            </FilterCapabilities>
          </Actions>
          ''')

        # Call the script with a mismatch.
        p = self.callHook(testhook,
                          self.repopath, self.username,
                          'MindRead:MergeInfo:Emote')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Capability missing',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertTrue(p.returncode != 0,
                        'Expected error exit code is zero')

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestFilterCapabilities)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
