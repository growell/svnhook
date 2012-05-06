#!/usr/bin/env python
######################################################################
# Test Non-Filter Actions
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

class TestActions(HookTestCase):

    def setUp(self):
        self.setUpTest(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_senderror(self):
        """Send simple error message."""
        errmsg = 'Something bad happened.'

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendError>{}</SendError>
          </Actions>
          '''.format(errmsg))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == 1,
            'Exit code not default (1): {}'.format(p.returncode))

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertEqual(
            stderrdata, errmsg,
            'Error output not correct: "{}"'.format(stderrdata))

    def test_02_senderror(self):
        """Send error with exit code."""
        exitcode = 2
        errmsg = 'Something else happened'

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendError exitCode="{}">{}</SendError>
          </Actions>
          '''.format(exitcode, errmsg))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == exitcode,
            'Exit code not correct: {}'.format(p.returncode))

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertEqual(
            stderrdata, errmsg,
            'Error output not correct: "{}"'.format(stderrdata))

    def test_03_settoken(self):
        """Set token."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SetToken name="happy">joy</SetToken>
          </Actions>
          ''')

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == 0,
            'Exit code is not correct: {}'.format(p.returncode))

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertEqual(
            stderrdata, '',
            'Error output not empty: "{}"'.format(stderrdata))

    def test_04_settoken(self):
        """Set and use token."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SetToken name="happy">joy</SetToken>
            <SendError>I feel ${happy}!</SendError>
          </Actions>
          ''')

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertEqual(
            stderrdata, 'I feel joy!',
            'Error output not correct: "{}"'.format(stderrdata))

    def test_05_settoken(self):
        """Set and use recursive token."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SetToken name="happy">joy</SetToken>
            <SetToken name="quote">I feel ${happy}!</SetToken>
            <SendError>She said, &quot;${quote}&quot;</SendError>
          </Actions>
          ''')

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')

        # Verify the proper error is returned.
        (stdoutdata, stderrdata) = p.communicate()
        self.assertEqual(
            stderrdata, 'She said, "I feel joy!"',
            'Error output not correct: "{}"'.format(stderrdata))

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestActions)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
