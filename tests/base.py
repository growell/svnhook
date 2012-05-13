#!/usr/bin/env python
######################################################################
# SvnHook Test Case Core Classes and Functions
######################################################################
__all__ = ['HookTestCase', 'SmtpTestCase', 'LogScanner', 'rmtree']

import re
import errno, os, sys, shutil, stat
import subprocess
import StringIO, mailbox, email
from textwrap import dedent
import unittest

from smtpsink import SmtpSink

# Define the data root.
datadir = os.path.normpath(os.path.join(
        os.path.dirname(__file__), 'data'))
tmpdir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'tmp'))

# If needed, create the temporary directory.
if not os.path.isdir(tmpdir): os.makedirs(tmpdir)

class HookTestCase(unittest.TestCase):
    """SvnHook Test Case Base Class"""

    def setUp(self, repoid, username='user', password='password'):
        """Initialize the test repository and working copy.

        Args:
            repoid: Identifier for the repository and data set.
            username: Working copy user name.
            password: Working copy password.

        """
        # Initialize the test attributes.
        self.repoid = repoid
        self.username = username
        self.password = password

        self.repopath = os.path.join(tmpdir, self.repoid + '-repo')
        if self.repopath[:1] == '/':
            self.repourl = 'file://' + self.repopath
        else:
            self.repourl = 'file:///'\
                + re.sub(r'\\', r'/', self.repopath)
        self.wcpath = os.path.join(tmpdir, self.repoid + '-wc')

        self.hooks = {}

        # If the repository already exists, delete it.
        if os.path.isdir(self.repopath): rmtree(self.repopath)
            
        # If the working copy already exists, delete it.
        if os.path.isdir(self.wcpath): rmtree(self.wcpath)
            
        # Construct the test repository.
        subprocess.check_call(['svnadmin', 'create', self.repopath])

        # Create the standard repository log file directory.
        os.mkdir(os.path.join(self.repopath, 'logs'))

        # Check for repository initialization data directory.
        repodata = os.path.join(datadir, repoid)
        if os.path.isdir(repodata):

            # Load the initialization files.
            for datafile in os.listdir(repodata):
                datapath = os.path.join(repodata, datafile)

                # Load a repository dump file.
                if datafile.endswith('.dmp'):
                    subprocess.check_call(
                        ['svnadmin', 'load', self.repopath],
                        stdin=open(datapath))

                # Load a hook configuration file.
                elif datafile.endswith('.conf')\
                        or datafile.endswith('.xml')\
                        or datafile.endswith('.yml'):
                    shutil.copy(
                        datapath, os.path.join(self.repopath, 'conf'))

                # Load a Windows (BAT) hook script.
                elif sys.platform.startswith('win')\
                        and datafile.endswith('.bat'):
                    hookname = datafile[:-4]
                    hookpath = os.path.join(
                        self.repopath, 'hooks', datafile)
                    shutil.copyfile(datapath, hookpath)
                    self.hooks[hookname] = hookpath

                # Load a Unix (shell) hook script.
                elif (not sys.platform.startswith('win'))\
                        and datafile.endswith('.sh'):
                    hookname = datafile[:-3]
                    hookpath = os.path.join(
                        self.repopath, 'hooks', hookname)
                    shutil.copy2(datapath, hookpath)
                    self.hooks[hookname] = hookpath

        # Create the initial working copy. Explicit credentials are
        # used to set the default commit user name.
        subprocess.check_call(
            ['svn', 'checkout', self.repourl, self.wcpath,
             '--non-interactive', '--username', self.username,
             '--password', self.password], stdout=subprocess.PIPE)

    def writeConf(self, filename, content, raw=False):
        """Write content into a repository configuration file.

        Args:
            filename: File name of the 'conf' directory file.
            content: Content to store in the file.
            raw: Flag request for no dedent.

        """
        filepath = os.path.join(self.repopath, 'conf', filename)
        with open(filepath, 'w') as f:
            if raw: f.write(content)
            else: f.write(dedent(content))

    def getLogScanner(self, filename):
        """Get the scanner object for a log file.

        Args:
            filename: File name of the 'logs' directory file.

        """
        return LogScanner(
            os.path.join(self.repopath, 'logs', filename))

    def callHook(self, hookname, *args, **kwargs):
        """Call a hook script directly.

        Args:
            hookname: Base name of the pre-loaded hook script.

        Returns: Subprocess object produced by hook script execution.

        """
        if hookname not in self.hooks:
            raise KeyError('Hook script not found: ' + hookname)
        cmd = [self.hooks[hookname]] + list(args)

        # Handle passing STDIN to the script.
        if 'stdin' in kwargs.keys():
            p = subprocess.Popen(cmd,
                                 stdin=kwargs['stdin'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)

        # Handle a script without STDIN data.
        else:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)

        # Wait for the script to finish.
        p.wait()

        # Pass back the process object.
        return p

    def addWcItem(self, pathname):
        """Schedule working copy items for addition.

        Args:
            pathname: Relative path name of the item.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(['svn', 'add', fullpath])

    def rmWcItem(self, pathname):
        """Schedule working copy items for deletion.

        Args:
            pathname: Relative path name of the item.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(['svn', 'rm', fullpath])

    def setWcProperty(self, propname, propval, pathname='.'):
        """Set a working copy property.

        Args:
            propname: Name of the property.
            propval: Value of the property.
            pathname: Relative path name of target.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(
            ['svn', 'propset', propname, propval, fullpath])

    def delWcProperty(self, propname, pathname='.'):
        """Delete a working copy property.

        Args:
            propname: Name of the property.
            pathname: Relative path name of target.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(
            ['svn', 'propdel', propname, fullpath])

    def revertWc(self):
        """Revert all working copy changes."""
        subprocess.check_call(['svn', 'revert', self.wcpath, '-R'])

    def commitWc(self, message='', *args, **kwargs):
        """Commit working copy changes.

        Args:
            message: Log message for commit.

        """
        options = ['-m', message]
        for option in sorted(kwargs.keys()):
            if option[:1] == '-': options.append(option)
            elif len(option) == 1: options.append('-' + option)
            else: options.append('--' + option)
            options.append(kwargs[option])

        subprocess.check_call(
            ['svn', 'commit', self.wcpath, options])

    def updateWc(self):
        """Update the entire working copy."""
        subprocess.check_call(['svn', 'update', self.wcpath])

    def makeWcFile(self, pathname, content=''):
        """Create/Replace a working copy file.

        Args:
            pathname: Relative path name of the file.
            content: Content of the file.

        """
        fullpath = os.path.join(self.wcpath, pathname)

        # Create any intermediate folders.
        os.mkdirs(os.path.dirname(fullpath))

        # Create/update the file.
        with open(fullpath, 'w') as f:
            f.write(content)

    def makeWcFolder(self, pathname):
        """Create/Replace a working copy folder.

        Args:
            pathname: Relative path name of the folder.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        if os.isdir(fullpath): rmtree(fullpath)
        os.mkdirs(fullpath)

    def addWcFile(self, pathname, content=''):
        """Create a working copy file and add it.

        Args:
            pathname: Relative path name of the file.
            content: Content of the file.

        """
        self.makeWcFile(pathname, content)
        self.addWcItem(pathname)

    def addWcFolder(self, pathname):
        """Create a working copy folder and add it.

        Args:
            pathname: Relative path name of the folder.

        """
        self.makeWcFolder(pathname)
        self.addWcItem(pathname)

class SmtpTestCase(HookTestCase):
    """SvnHook Test Case with SMTP Server"""

    def setUp(self, port=8025, *args, **kwargs):
        # Initialize the base test case.
        super(SmtpTestCase, self).setUp(*args, **kwargs)

        # Construct the SMTP server.
        self.smtpaddress = 'localhost', port
        self.smtpserver = SmtpSink(port=port)

        # Start the SMTP server thread.
        self.smtpserver.start()

        # Make sure the SMTP server is always shut down.
        self.addCleanup(_stopSmtpServer, self)

    def _stopSmtpServer(self):
        # Stop the SMTP server thread.
        self.smtpserver.stop()

    def getMailbox(self):
        """Get the Unix mailbox object containing received
        messages."""
        # Load the mailbox contents into an IO object.
        mailboxFile =  StringIO.StringIO(
            self.smtpserver.getMailboxContents())

        # Construct a mailbox object from the contents.
        return mailbox.PortableUnixMailbox(
            mailboxFile, email.message_from_file)

    def assertSubjectIn(self, subject, msg=None):
        """Assert that a received message has the exact subject
        line.

        Args:
            subject: Subject line of the message.
            msg: Optional message to use on failure.

        """
        # Get the subject lines of the messages.
        subjects = [re.match(
                r'^Subject: (.+)$', message.as_string(), re.MULTILINE)
                    for message in self.getMailbox()]

        # Apply the assertion.
        self.assertIn(subject, subjects, msg)

    def assertBodyRegexpIn(self, regex, msg=None):
        """Assert that a regular expression is in a received message
        body. Header lines are not searched.

        Args:
            regex: Regular expression to search with.
            msg: Optional message to use on failure.

        """
        # Defined the default failure message.
        if msg == None:
            msg = 'Regular expression not matched'\
                ' by message bodies: ' + re

        # Get the body sections of the messages.
        bodies = [re.search(
                r'\n\n(.+)$', message.as_string(), re.DOTALL)
                  for message in self.getMailbox()]

        # Search through the bodies for a match.
        regexobj = re.compile(regex)
        for body in bodies:
            if regexobj.search(body) != None: return

        # A match wasn't found. Indicate a failure.
        self.fail(msg)

class LogScanner(object):
    """SvnHook Log File Scanner"""

    def __init__(self, pathname):
        """Mark the end position of the log file.

        Args:
            pathname: Path name of the log file.

        """
        self.pathname = pathname

        # Mark the current EOF.
        with open(pathname) as f:
            f.seek(0, os.SEEK_END)
            self.position = f.tell()

    def read(self):
        """Get the added log file content."""
        # Get the added content. Update the saved position.
        with open(self.pathname) as f:
            f.seak(self.position, os.SEEK_SET)
            content = f.read()
            self.position = f.tell()

        return content

# Under Windows, the "shutil.rmtree" function fails upon encountering
# read-only files. These functions isolate callers from these details.

def _rmtree_onerror(func, path, excinfo):
    """Handle an rmtree read-only error.

    Args:
        func: Calling function.
        path: Path name of the target.
        excinfo: Exception information.

    """
    excvalue = excinfo[1]
    if func in (os.rmdir, os.remove)\
            and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)
        func(path)
    else:
        raise

def rmtree(path):
    """Reliably remove a non-empty directory.

    Args:
        path: Path name of the directory.

    """
    shutil.rmtree(path, onerror=_rmtree_onerror)
    
########################### end of file ##############################
