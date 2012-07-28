#!/usr/bin/env python
######################################################################
# Test Lock Comment Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterComment(HookTestCase):
    """Comment Filter Tests"""

    def setUp(self):
        super(TestFilterComment, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex_tag(self):
        """Comment regex missing."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterComment>
              <SendError>Lock comment not allowed.</SendError>
            </FilterComment>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, '', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'Internal hook error',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertEqual(
<<<<<<< HEAD
            p.returncode & 0x7f, 0x7f,
            'Error exit code not found: exit code = {0}'\
                .format(p.returncode))
=======
            p.returncode, 255,
            'Unexpected exit code found')
>>>>>>> origin/master

    def test_02_match_true(self):
        """Comment regex true match."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterComment>
              <CommentRegex>world</CommentRegex>
              <SendError>World comments not allowed.</SendError>
            </FilterComment>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, 'Hello world!', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'World comments not allowed',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Expected exit code not found')

    def test_03_match_false(self):
        """Comment regex false match."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterComment>
              <CommentRegex sense="false">world</CommentRegex>
              <SendError>World comments required.</SendError>
            </FilterComment>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, 'Hello, Joe!', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify the proper error message is returned.
        self.assertRegexpMatches(
            stderrdata, r'World comments required',
            'Expected error message not found')

        # Verify a failure is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Expected exit code not found')

    def test_04_start_mismatch(self):
        """Comment regex start mismatch."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterComment>
              <CommentRegex>^world</CommentRegex>
              <SendError>World comments not allowed.</SendError>
            </FilterComment>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, 'Hello world!', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify a failure isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Expected exit code not found')

        # Verify an error message isn't returned.
<<<<<<< HEAD
        self.assertRegexpMatches(
            stderrdata, r'(?s)^\s*$',
=======
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
>>>>>>> origin/master
            'Unexpected error message found')

    def test_05_end_mismatch(self):
        """Comment regex end mismatch."""

        # Define the hook configuration.
        self.writeConf('pre-lock.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterComment>
              <CommentRegex>world$</CommentRegex>
              <SendError>World comments not allowed.</SendError>
            </FilterComment>
          </Actions>
          ''')

        # Call the script.
        p = self.callHook(
            'pre-lock', self.repopath, '/file1.txt',
            self.username, 'Hello world!', 0)
        (stdoutdata, stderrdata) = p.communicate()
        p.wait()

        # Verify a failure isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Expected exit code not found')

        # Verify an error message isn't returned.
<<<<<<< HEAD
        self.assertRegexpMatches(
            stderrdata, r'(?s)^\s*$',
=======
        self.assertNotRegexpMatches(
            stderrdata, r'\S',
>>>>>>> origin/master
            'Unexpected error message found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterComment]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
