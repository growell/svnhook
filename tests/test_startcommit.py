#!/usr/bin/env python
######################################################################
# Test start-commit Hook Processing
######################################################################
import inspect, os, re, sys
from textwrap import dedent
import unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase
from svnhook.hooks import StartCommit

class TestStartCommit(HookTestCase):

    def setUp(self):
        repoid = re.sub(r'^.+\.test_', '', __name__)
        super(TestStartCommit, self).setUp(repoid)

    def test_senderror(self):
        """Able to send error messages."""
        # Define the hook configuration.
        self.writeConf('start-commit.xml', dedent('''\
          <?xml version="1.0"?>
          <Actions>
            <SendError>Something bad happened.</SendError>
          </Actions>
          '''))

        # Call the script with a mismatch.
        p = self.callHook('start-commit',
                          self.repopath, self.username, '')

        # Verify a failure is indicated.
        self.assertTrue(p.returncode != 0,
                        'Exit code is zero.')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Something bad happened')


    def test_capabilities(self):
        """Detect missing 'mergeinfo' capability."""
        # Define the hook configuration.
        self.writeConf('start-commit.xml', dedent('''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCapabilities>
              <CapabilitiesRegex sense="false">mergeinfo</CapabilitiesRegex>
              <SendError>Capability missing: mergeinfo</SendError>
            </FilterCapabilities>
          </Actions>
          '''))

        # Call the script with a mismatch.
        p = self.callHook('start-commit',
                          self.repopath, self.username, '')

        # Verify a failure is indicated.
        self.assertTrue(p.returncode != 0,
                        'Exit code is zero')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertRegexpMatches(
            stderrdata, r'Capability missing')

# Allow manual execution.
if __name__=='__main__':
    unittest.main()

########################### end of file ##############################
