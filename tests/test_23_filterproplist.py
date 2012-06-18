#!/usr/bin/env python
######################################################################
# Test Property List Filter
######################################################################
import os, re, sys, unittest, time

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

class TestFilterPropList(HookTestCase):
    """Pre-Commit Property List Filter Tests"""

    def setUp(self):
        super(TestFilterPropList, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tags"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <SendError>You're bothering me.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('junk', '*', 'fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated. Please note that this is
        # NOT the hook script exit code. This is the "svn commit" exit
        # code - that indicates if the commit succeeded (zero) or
        # failed (one).
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Internal hook error',
            'Internal error message not returned')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-commit', r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_name_match(self):
        """Property name match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropNameRegex>junk</PropNameRegex>
                <SendError>Cannot mark as junk.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('junk', '*', 'fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot mark as junk',
            'Expected error message not returned')

    def test_03_name_mismatch(self):
        """Property name mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropNameRegex>junk</PropNameRegex>
                <SendError>Cannot mark as junk.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('zjunk', '*', 'fileA1.txt')

        # Attempt to commit the changes.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that an error message isn't sent.
        self.assertNotRegexpMatches(
            p.stderr.read(), r'\S',
            'Unexpected error message found')

    def test_04_value_match(self):
        """Property value match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropValueRegex>junk</PropValueRegex>
                <SendError>Cannot use junk value.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('zot', 'junk', 'fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot use junk value',
            'Expected error message not returned')

    def test_05_value_mismatch(self):
        """Property value mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropValueRegex>junk</PropValueRegex>
                <SendError>Cannot mark as junk.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('zot', 'blah', 'fileA1.txt')

        # Attempt to commit the changes.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that an error message isn't sent.
        self.assertNotRegexpMatches(
            p.stderr.read(), r'\S',
            'Unexpected error message found')

    def test_06_both_match(self):
        """Property name and value match"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropNameRegex>stuff</PropNameRegex>
                <PropValueRegex>junk</PropValueRegex>
                <SendError>Cannot use junk value for stuff.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('stuffing', 'some junk', 'fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot use junk value for stuff',
            'Expected error message not returned')

    def test_07_both_mismatch(self):
        """Property name and value mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>.*</PathRegex>
              <FilterPropList>
                <PropNameRegex>stuff</PropNameRegex>
                <PropValueRegex>^junk</PropValueRegex>
                <SendError>Cannot use junk value for stuff.</SendError>
              </FilterPropList>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.setWcProperty('stuffing', 'some junk', 'fileA1.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {}'.format(p.returncode))

        # Verify that an error message is provided.
        self.assertNotRegexpMatches(
            p.stderr.read(), r'\S',
            'Unexpected error message returned')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterPropList]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
