#!/usr/bin/env python
######################################################################
# Test Revision Property Filter
######################################################################
import os, re, sys, unittest, time

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase

class TestFilterRevProp(HookTestCase):
    """Pre-RevProp-Change Property Filter Tests"""

    def setUp(self):
        super(TestFilterRevProp, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tags"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <SendError>Can't touch this.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'junk', '*')

        # Verify that an error is indicated. Please note that this is
        # NOT the hook script exit code. This is the "svn propset" exit
        # code - that indicates if the commit succeeded (zero) or
        # failed (one).
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Internal hook error',
            'Internal error message not returned')

        # Verify that the detailed error is logged.
        self.assertLogRegexp(
            'pre-revprop-change',
            r'\nValueError: Required tag missing',
            'Expected error not found in hook log')

    def test_02_name_match(self):
        """Property name match"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropNameRegex>junk</PropNameRegex>
              <SendError>Cannot mark as junk.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'junk', '*')

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot mark as junk',
            'Expected error message not returned')

    def test_03_name_mismatch(self):
        """Property name mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropNameRegex>junk</PropNameRegex>
              <SendError>Cannot mark as junk.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'zjunk', '*')

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message isn't sent.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
            'Unexpected error message found')

    def test_04_value_match(self):
        """Property value match"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropValueRegex>junk</PropValueRegex>
              <SendError>Cannot use junk value.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'zot', 'some junk')

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot use junk value',
            'Expected error message not returned')

    def test_05_value_mismatch(self):
        """Property value mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropValueRegex>junk</PropValueRegex>
              <SendError>Cannot mark as junk.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'zot', 'something else')

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message isn't sent.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
            'Unexpected error message found')

    def test_06_both_match(self):
        """Property name and value match"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropNameRegex>stuff</PropNameRegex>
              <PropValueRegex>junk</PropValueRegex>
              <SendError>Cannot use junk value for stuff.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'stuffing', 'some junk')

        # Verify that an error is indicated.
        self.assertEqual(
            p.returncode, 1,
            'Error exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that the proper error is indicated.
        self.assertRegexpMatches(
            p.stderr.read(), r'Cannot use junk value for stuff',
            'Expected error message not returned')

    def test_07_both_mismatch(self):
        """Property name and value mismatch"""

        # Define the hook configuration.
        self.writeConf('pre-revprop-change.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterRevProp>
              <PropNameRegex>stuff</PropNameRegex>
              <PropValueRegex>^junk</PropValueRegex>
              <SendError>Cannot use junk value for stuff.</SendError>
            </FilterRevProp>
          </Actions>
          ''')

        # Apply a revision property change.
        p = self.setRevProperty(1, 'stuffing', 'some junk')

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
                ' exit code = {0}'.format(p.returncode))

        # Verify that an error message is provided.
        self.assertRegexpMatches(
            p.stderr.read(), r'(?s)^\s*$',
            'Unexpected error message returned')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterRevProp]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
