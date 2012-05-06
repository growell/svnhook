#!/usr/bin/env python
######################################################################
# Test start-commit Hook Processing
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

class TestStartCommit(HookTestCase):

    def setUp(self):
        self.setUpTest(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_capabilities(self):
        """Detect missing 'mergeinfo' capability."""
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

        # Verify a failure is indicated.
        self.assertTrue(p.returncode != 0,
                        'Exit code is zero.')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Capability missing',
            'Expected error message not found.')

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestStartCommit)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
