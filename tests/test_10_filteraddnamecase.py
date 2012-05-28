#!/usr/bin/env python
######################################################################
# Test Name Case Change Filter
######################################################################
import os, re, sys, unittest
from subprocess import CalledProcessError

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from tests.base import HookTestCase

class TestFilterAddNameCase(HookTestCase):

    def setUp(self):
        super(TestFilterAddNameCase, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_baseline(self):
        """Add a file that shouldn't cause a conflict."""
        # The test suite files include a hook configuration that
        # uses the tested filter. This filter requires no inputs,
        # other than a pending transaction.

        # Add a file that shouldn't conflict with existing items.
        self.addWcFile('fileA2.txt')

        # Attempt to commit the change.
        p = self.commitWc()
        self.assertEqual(
            p.returncode, 0,
            'Failed to add non-conflicting file.')

    def test_02_replace(self):
        """Replace a file. This shouldn't case a conflict."""
        # Remove an existing file.
        self.rmWcItem('fileA.txt')

        # Replace it with another existing file.
        self.mvWcItem('fileB.txt', 'fileA.txt')

        # Attempt to commit the change.
        p = self.commitWc()
        self.assertEqual(
            p.returncode, 0,
            'Failed to replace non-conflicting file.')

    def test_03_file_conflict(self):
        """Add a file with a different name case."""
        # File-system remove the existing file.
        self.rmWcFsFile('fileA.txt')

        # Add a file with a different casing of the name.
        self.addWcFile('FileA.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Check for the expected failure.
        self.assertNotEqual(
            p.returncode, 0,
            'Expected non-zero exit code not found!')

        # Check for the expected error details (via SendError).
        errstr = p.stderr.read()
        self.assertRegexpMatches(errstr, r'Name case conflict')
        self.assertRegexpMatches(errstr, r'Folder\.+: /')
        self.assertRegexpMatches(errstr, r'Existing: fileA\.txt')
        self.assertRegexpMatches(errstr, r'Added\.+: FileA\.txt')

# Allow manual execution of tests.
if __name__=='__main__':
    suite = unittest.TestLoader()\
        .loadTestsFromTestCase(TestFilterAddNameCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
