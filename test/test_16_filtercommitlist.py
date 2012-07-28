#!/usr/bin/env python
######################################################################
# Test Commit List Filter
######################################################################
import os, re, sys, unittest, time

# Prefer local modules.
mylib = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..'))
if os.path.isdir(mylib): sys.path.insert(0, mylib)

from test.base import HookTestCase, SmtpTestCase

class TestFilterCommitList(HookTestCase):
    """Pre-Commit (Non-SMTP) Tests"""

    def setUp(self):
        super(TestFilterCommitList, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_01_no_regex(self):
        """No regex tags"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <SendError>You're bothering me.</SendError>
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

    def test_02_chgtype_match(self):
        """Change type match"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <ChgTypeRegex>A</ChgTypeRegex>
              <SendError>Adding content not allowed.</SendError>
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
            p.stderr.read(), r'Adding content not allowed',
            'Expected error message not returned')

    def test_03_not_chgtype_match(self):
        """Change type false match"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <ChgTypeRegex sense="False">A</ChgTypeRegex>
              <SendError>Only adding content allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add content. This should be ignored.
        self.addWcFile('fileA1.txt')

        # Modify a working copy property. This should send the error.
        self.setWcProperty('svn:ignore', '*.tmp')

        # Attempt to commit the changes.
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
            p.stderr.read(), r'Only adding content allowed',
            'Expected error message not returned')

    def test_04_path_match(self):
        """Path match"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>A2</PathRegex>
              <SendError>A2 content not allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes.
        self.addWcFile('fileA1.txt')
        self.addWcFile('fileA2.txt')

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
            p.stderr.read(), r'A2 content not allowed',
            'Expected error message not returned')

    def test_05_cs_path_mismatch(self):
        """Case-sensitive path mismatch"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>A2</PathRegex>
              <SendError>A2 content not allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes.
        self.addWcFile('file-A1.txt')
        self.addWcFile('file-a2.txt')

        # Attempt to commit the change.
        p = self.commitWc()

        # Verify that an error is indicated.
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
            'Unexpected error message returned')

    def test_06_ci_path_match(self):
        """Case-insensitive path match"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>(?i)A2</PathRegex>
              <SendError>A2 content not allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes.
        self.addWcFile('file-A1.txt')
        self.addWcFile('file-a2.txt')

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
            p.stderr.read(), r'A2 content not allowed',
            'Expected error message not returned')

    def test_07_folder_match(self):
        """Folder path match"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>A2/$</PathRegex>
              <SendError>A2 folder not allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes.
        self.addWcFile('fileA2')
        self.addWcFolder('folderA2')

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
            p.stderr.read(), r'A2 folder not allowed',
            'Expected error message not returned')

    def test_08_folder_mismatch(self):
        """Folder path mismatch"""
        # Define the hook configuration.
        self.writeConf('pre-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <PathRegex>A2/$</PathRegex>
              <SendError>A2 folder not allowed.</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add working copy changes (that don't trigger the error).
        self.addWcFile('fileA2')
        self.addWcFolder('folderA1')

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
            'Unexpected error message returned')

class TestFilterCommitList2(SmtpTestCase):
    """Post-Commit (SMTP) Tests"""

    def setUp(self):
        super(TestFilterCommitList2, self).setUp(
            re.sub(r'^test_?(.+)\.[^\.]+$', r'\1',
                   os.path.basename(__file__)))

    def test_09_post_error(self):
        """Post-commit error"""
        # Define the hook configuration.
        self.writeConf('post-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList>
              <ChgTypeRegex>A</ChgTypeRegex>
              <SendError>Now you did it!</SendError>
            </FilterCommitList>
          </Actions>
          ''')

        # Add a working copy change.
        self.addWcFile('fileA1.txt')

        # Commit the change.
        p = self.commitWc()

        # Verify that an error isn't indicated. Because the problem is
        # detected AFTER the commit, it indicates success and returns
        # a STDOUT advisory message.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Verify that the proper advisory is indicated.
        self.assertRegexpMatches(
            p.stdout.read(), r'Now you did it',
            'Expected advisory message not returned')

    def test_10_match_first(self):
        """Trigger only once"""
        # Define the message parameters.
        now = str(time.asctime())
        subject = '${Path} @ ' + now

        # Define the hook configuration.
        self.writeConf('post-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList matchFirst="true">
              <PathRegex>/$</PathRegex>
<<<<<<< HEAD
              <SendSmtp port="{0}">
                <FromAddress>source@mydomain.com</FromAddress>
                <ToAddress>destination@yourdomain.com</ToAddress>
                <Subject>{1}</Subject>
=======
              <SendSmtp port="{}">
                <FromAddress>source@mydomain.com</FromAddress>
                <ToAddress>destination@yourdomain.com</ToAddress>
                <Subject>{}</Subject>
>>>>>>> origin/master
                <Message>Folder is added/modified.</Message>
              </SendSmtp>
            </FilterCommitList>
          </Actions>
          '''.format(self.smtpport, subject))

        # Apply working copy changes.
        self.addWcFile('fileA.txt')
        self.addWcFolder('folderA1')
        self.addWcFolder('folderA2')

        # Commit the changes.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Look for the first folder email message. It should be found.
        try:
            message = self.getMessage(
                subject='folderA1/ @ ' + now)
        except KeyError:
            self.fail('Expected folderA1 email message not found')

        # Look for the second folder email message. It should not be
        # found.
        try:
            message = self.getMessage(
                subject='folderA2/ @ ' + now)
            self.fail('Unexpected folderA2 email message found')
        except KeyError:
            pass

    def test_11_match_all(self):
        """Trigger for each match"""
        # Define the message parameters.
        now = str(time.asctime())
        subject = '${Path} @ ' + now

        # Define the hook configuration.
        self.writeConf('post-commit.xml', '''\
          <?xml version="1.0"?>
          <Actions>
            <FilterCommitList matchFirst="false">
              <PathRegex>/$</PathRegex>
<<<<<<< HEAD
              <SendSmtp port="{0}">
                <FromAddress>source@mydomain.com</FromAddress>
                <ToAddress>destination@yourdomain.com</ToAddress>
                <Subject>{1}</Subject>
=======
              <SendSmtp port="{}">
                <FromAddress>source@mydomain.com</FromAddress>
                <ToAddress>destination@yourdomain.com</ToAddress>
                <Subject>{}</Subject>
>>>>>>> origin/master
                <Message>Folder is added/modified.</Message>
              </SendSmtp>
            </FilterCommitList>
          </Actions>
          '''.format(self.smtpport, subject))

        # Apply working copy changes.
        self.addWcFile('fileA.txt')
        self.addWcFolder('folderA1')
        self.addWcFolder('folderA2')

        # Commit the changes.
        p = self.commitWc()

        # Verify that an error isn't indicated.
        self.assertEqual(
            p.returncode, 0,
            'Success exit code not found:'\
<<<<<<< HEAD
                ' exit code = {0}'.format(p.returncode))
=======
                ' exit code = {}'.format(p.returncode))
>>>>>>> origin/master

        # Look for the first folder email message. It should be found.
        try:
            message = self.getMessage(
                subject='folderA1/ @ ' + now)
        except KeyError:
            self.fail('Expected folderA1 email message not found')

        # Look for the second folder email message. It should be
        # found, too.
        try:
            message = self.getMessage(
                subject='folderA2/ @ ' + now)
        except KeyError:
            self.fail('Expected folderA2 email message not found')

# Allow manual execution of tests.
if __name__=='__main__':
    for tclass in [TestFilterCommitList, TestFilterCommitList2]:
        suite = unittest.TestLoader().loadTestsFromTestCase(tclass)
        unittest.TextTestRunner(verbosity=2).run(suite)

########################### end of file ##############################
