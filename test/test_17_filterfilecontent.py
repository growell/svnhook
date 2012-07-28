#!/usr/bin/env python
######################################################################
# Test File Content Filter
######################################################################
import os, re, sys, unittest

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterFileContent(HookTestCase):
    """File Content Filter Tests"""

    def setUp(self):
        super(TestFilterFileContent, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tag"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <SendError>Not gonna happen.</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated. Please note that this is
        # NOT the hook script exit code. This is the "svn commit" exit
        # code - that indicates if the commit succeeded (zero) or
        # failed (one).
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Internal hook error',
            'Internal error message not returned')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-commit', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_true_match(self):
        """Positive content match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <ContentRegex>\S</ContentRegex>
                <SendError>How high?</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt', 'Jump.\n')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'How high\?',
            'Expected error message not found')

    def test_03_true_mismatch(self):
        """Positive content mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <ContentRegex>\S</ContentRegex>
                <SendError>How high?</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt', '\n')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message isn't returned.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
=======
                ' exit code = {}'.format(p.returncode))

        # Verify that an error message isn't returned.
        self.assertNotRegexpMatches(
            p.stderr.read(), r'\S',
>>>>>>> origin/master
            'Unexpected error message found')

    def test_04_false_match(self):
        """Negative content match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <ContentRegex sense="0">\S</ContentRegex>
                <SendError>What is your question?</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'What is your question\?',
            'Expected error message not found')

    def test_05_false_mismatch(self):
        """Negative content mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <ContentRegex sense="0">\S</ContentRegex>
                <SendError>What is your question?</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt', 'Hunh?\n')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message isn't returned.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
=======
                ' exit code = {}'.format(p.returncode))

        # Verify that an error message isn't returned.
        self.assertNotRegexpMatches(
            p.stderr.read(), r'\S',
>>>>>>> origin/master
            'Unexpected error message found')

    def test_06_folder_ignore(self):
        """Ignore changed folders"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList> <!-- Need PATH input. -->
              <PathRegex>.+</PathRegex>
              <FilterFileContent>
                <ContentRegex>\S</ContentRegex>
                <SendError>This is evil.</SendError>
              </FilterFileContent>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes that include a folder. Put a file
        # that matches the condition in the new folder.
        self.addWcFile('fileA1.txt')
        self.addWcFolder('folderA2')
        self.addWcFile('folderA2/fileA2.txt', 'Boo.\n')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the error message is returned.
        self.assertRegexpMatches(
            p.stderr.read(), r'This is evil',
            'Expected error message not found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterFileContent]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
