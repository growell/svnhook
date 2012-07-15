#!/usr/bin/env python
######################################################################
# Test Basic Non-Filter Revision Actions
######################################################################
import os, re, sys, unittest
import subprocess, random

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

# Test Hook and Configuration File
testhook = 'post-commit'
testconf = 'post-commit.xml'

class TestActions(HookTestCase):

    def setUp(self):
        super(TestActions, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

        # Generate a random revision number string.
        self.revision = str(random.randint(10000, 99999))

    def test_01_setrevisionfile(self):
        """Save revision number in a file."""
        # Make sure the revision file doesn't exist.
        revisionfile = os.path.join(self.repopath, 'revision-flag.txt')
        if os.path.isfile(revisionfile): os.rm(revisionfile)

        # Define the hook configuration.
        self.writeConf(testconf, '''\
          <?xml version="1.0"?>
          <Actions>
            <SetRevisionFile>{0}</SetRevisionFile>
          </Actions>
          '''.format(revisionfile))

        # Call the script that uses the configuration.
        p = self.callHook(testhook, self.repopath, self.revision)
        p.wait()

        # Check for the default exit code.
        self.assertEqual(
            p.returncode, 0,
            'Exit code not correct: {0}'.format(p.returncode))

        # Verify that the revision file now exists.
        self.assertTrue(os.path.isfile(revisionfile),
                        'Revision file not found: ' + revisionfile)

        # Check the revision file contents.
        contents = open(revisionfile).read().rstrip()
        self.assertEqual(
            contents, self.revision,
            'Revision file contents not correct: {0}'.format(contents))

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestActions)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
