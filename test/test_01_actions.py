#!/usr/bin/env python
######################################################################
# Test Basic Non-Filter Actions
######################################################################
import os, re, sys, unittest
import subprocess

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

# Test Hook and Configuration File
testhook = 'start-commit'
testconf = 'start-commit.xml'

class TestActions(HookTestCase):

    def setUp(self):
        super(TestActions, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_senderror(self):
        """Send simple error message."""
        errmsg = 'Something bad happened.'

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendError>{0}</SendError>
          </Actions>
          '''.format(errmsg))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == 1,
            'Exit code not default (1): {0}'.format(p.returncode))

        # Verify the proper error is returned.
        self.assertEqual(
            stderrdata, errmsg,
            'Error output not correct: "{0}"'.format(stderrdata))

    def test_02_senderror(self):
        """Send error with exit code."""
        exitcode = 2
        errmsg = 'Something else happened'

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SendError exitCode="{0}">{1}</SendError>
          </Actions>
          '''.format(exitcode, errmsg))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == exitcode,
            'Exit code not correct: {0}'.format(p.returncode))

        # Verify the proper error is returned.
        self.assertEqual(
            stderrdata, errmsg,
            'Error output not correct: "{0}"'.format(stderrdata))

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
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == 0,
            'Exit code is not correct: {0}'.format(p.returncode))

        # Verify the proper error is returned.
        self.assertEqual(
            stderrdata, '',
            'Error output not empty: "{0}"'.format(stderrdata))

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
            'Error output not correct: "{0}"'.format(stderrdata))

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
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error is returned.
        self.assertEqual(
            stderrdata, 'She said, "I feel joy!"',
            'Error output not correct: "{0}"'.format(stderrdata))

    def test_06_executecmd(self):
        """Execute a successful system command."""
        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <ExecuteCmd><![CDATA[{0} --version]]></ExecuteCmd>
          </Actions>
          '''.format(sys.executable))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        p.wait()

        # Check for the default exit code.
        self.assertTrue(
            p.returncode == 0,
            'Exit code is not correct: {0}'.format(p.returncode))

    def test_07_executecmd(self):
        """Execute an unmasked failing system command."""
        # Define the hook configuration.
        exitcode = 2
        cmdline = '{0} -c "exit({1})"'.format(sys.executable, exitcode)
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <ExecuteCmd errorLevel="2"><![CDATA[{0}]]></ExecuteCmd>
          </Actions>
          '''.format(cmdline))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        p.wait()

        # Check for the expected exit code.
        self.assertTrue(
            p.returncode == exitcode,
            'Exit code is not correct: {0}'.format(p.returncode))

    def test_08_executecmd(self):
        """Execute a masked failing system command."""
        # Define the hook configuration.
        cmdline = '{0} -c "exit(2)"'.format(sys.executable)
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <ExecuteCmd errorLevel="3"><![CDATA[{0}]]></ExecuteCmd>
          </Actions>
          '''.format(cmdline))

        # Call the script that uses the configuration.
        p = self.callHook(testhook,
                          self.repopath, self.username, '')
        p.wait()

        # Check for the expected exit code.
        self.assertTrue(
            p.returncode == 0,
            'Exit code is not correct: {0}'.format(p.returncode))

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestActions)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
