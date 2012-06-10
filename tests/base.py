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
import unittest, pprint

from smtpsink import SmtpSink

# Define the directory locations.
datadir = os.path.normpath(os.path.join(
        os.path.dirname(__file__), 'data'))
tmpdir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'tmp'))

# If needed, create the temporary directory.
if not os.path.isdir(tmpdir): os.makedirs(tmpdir)

class HookTestCase(unittest.TestCase):
    """SvnHook Test Case Base Class"""

    # Per-Suite Test Case Indexes
    tcindexes = dict()

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
        self.hooks = {}

        # Allocate a test case index.
        try:
            HookTestCase.tcindexes[self.repoid] += 1
        except KeyError:
            HookTestCase.tcindexes[self.repoid] = 1

        self.tcindex = HookTestCase.tcindexes[self.repoid]
        
        # Construct the test artifact directory.
        workdir = os.path.join(
            tmpdir, '{}.{:02d}'.format(self.repoid, self.tcindex))
        if os.path.isdir(workdir): rmtree(workdir)
        os.makedirs(workdir)

        # Define the working repository.
        self.repopath = os.path.join(workdir, 'repo')
        if self.repopath[:1] == '/':
            self.repourl = 'file://' + self.repopath
        else:
            self.repourl = 'file:///'\
                + re.sub(r'\\', r'/', self.repopath)

        # Define the working copy.
        self.wcpath = os.path.join(workdir, 'wc')

        # Construct the test repository.
        subprocess.check_output(['svnadmin', 'create', self.repopath])

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
                    subprocess.check_output(
                        ['svnadmin', 'load', self.repopath,
                         '--force-uuid', '--quiet'],
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
        subprocess.check_output(
            ['svn', 'checkout', self.repourl, self.wcpath,
             '--non-interactive', '--username', self.username,
             '--password', self.password])

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

    def getHookLog(self, hookname):
        """Get the log file path name for a hook script.

        Args:
            hookname: Base name of the hook script.

        Returns: Path name of the log file.
        """
        return os.path.join(
            self.repopath, 'logs', hookname + '.log')

    def assertLogRegexp(self, hookname, regexp, msg=None):
        """Assert that hook log matches a regular expression.

        Args:
            hookname: Base name of the hook script.
            regexp: Regular expression to search for.
            msg: Assertion message when not matched.
        """
        with open(self.getHookLog(hookname)) as f:
            self.assertRegexpMatches(f.read(), regexp, msg)

    def assertLogNotRegexp(self, hookname, regexp, msg=None):
        """Assert that hook log doesn't match a regular expression.

        Args:
            hookname: Base name of the hook script.
            regexp: Regular expression to search for.
            msg: Assertion message when matched.
        """
        with open(self.getHookLog(hookname)) as f:
            self.assertNotRegexpMatches(f.read(), regexp, msg)

    def callHook(self, hookname, *args, **kwargs):
        """Call a hook script directly.

        Args:
            hookname: Base name of the pre-loaded hook script.

        Returns: Subprocess object produced by hook script execution.
        """
        if hookname not in self.hooks:
            raise KeyError('Hook script not found: ' + hookname)
        cmd = [self.hooks[hookname]] + map(str, args)

        # Start the hook script process.
        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False)

        # Pass back the running process object.
        # NOTE: We don't wait for it to finish, because it may be
        #       waiting on some data from STDIN.
        return p

    def makeRepoFolder(self, pathname, *args, **kwargs):
        """Directly add a folder to the repository.

        Args:
            pathname: Relative path name of the folder.

        Returns: Process object used to add the folder.
        """
        # Default the commit message to an empty string.
        try:
            message = kwargs['message']
            del kwargs['message']
        except KeyError:
            message = ''

        # Construct the base command.
        fullurl = '/'.join([self.repourl, pathname])
        cmd = ['svn', 'mkdir', fullurl, '-m', message]

        # Apply any non-value options.
        for arg in args:
            if arg[:1]=='-': cmd.append(arg)
            elif len(arg)==1: cmd.append('-' + arg)
            else: cmd.append('--' + arg)

        # Apply any valued options.
        for option in sorted(kwargs.keys()):
            if len(option)==1: cmd.append('-' + option)
            else: cmd.append('--' + option)
            cmd.append(kwargs[option])

        # Start the command. Wait for it to finish. A hook failure
        # should run the command, but return a non-zero exit code.
        # Details should be provided via the STDERR pipe.
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        return p

    def addWcItem(self, pathname):
        """Schedule working copy items for addition.

        Args:
            pathname: Relative path name of the item.

        Returns: Output produced by Subversion command.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        return subprocess.check_output(['svn', 'add', fullpath])

    def cpWcItem(self, srcpathname, destpathname):
        """Copy a working copy item.

        Args:
            srcpathname: Relative path name of the source item.
            destpathname: Relative path name of the destination.

        Returns: Output produced by Subversion command.
        """
        source = os.path.join(self.wcpath, srcpathname)
        destination = os.path.join(self.wcpath, destpathname)
        return subprocess.check_output(
            ['svn', 'cp', source, destination])

    def mvWcItem(self, srcpathname, destpathname):
        """Move/Rename a working copy item.

        Args:
            srcpathname: Relative path name of the source item.
            destpathname: Relative path name of the destination.

        Returns: Output produced by Subversion command.
        """
        source = os.path.join(self.wcpath, srcpathname)
        destination = os.path.join(self.wcpath, destpathname)
        return subprocess.check_output(
            ['svn', 'mv', source, destination])

    def rmWcItem(self, pathname):
        """Schedule working copy items for deletion.

        Args:
            pathname: Relative path name of the item.

        Returns: Output produced by Subversion command.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        return subprocess.check_output(['svn', 'rm', fullpath])

    def rmWcFsFile(self, pathname):
        """Remove a working copy file without scheduling it for
        removal from Subversion.

        Args:
            pathname: Relative path name of the file.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        os.remove(fullpath)

    def rmWcFsDir(self, pathname):
        """Recursively remove a working copy directory without
        scheduling it for removal from Subversion.

        Args:
            pathname: Relative path name of the directory.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        rmtree(fullpath)

    def setWcProperty(self, propname, propval, pathname='.'):
        """Set a working copy property.

        Args:
            propname: Name of the property.
            propval: Value of the property.
            pathname: Relative path name of target.

        Returns: Output produced by Subversion command.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        return subprocess.check_output(
            ['svn', 'propset', propname, propval, fullpath])

    def delWcProperty(self, propname, pathname='.'):
        """Delete a working copy property.

        Args:
            propname: Name of the property.
            pathname: Relative path name of target.

        Returns: Output produced by Subversion command.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        return subprocess.check_output(
            ['svn', 'propdel', propname, fullpath])

    def revertWc(self):
        """Revert all working copy changes.

        Returns: Output produced by Subversion command.
        """
        return subprocess.check_output(
            ['svn', 'revert', self.wcpath, '-R'])

    def commitWc(self, *args, **kwargs):
        """Commit working copy changes.

        Args:
            *args: Additional commit arguments.
            **kwargs: Additional named options.

        Returns: Process object that ran Subversion command.
        """
        # Default the commit message to an empty string.
        try:
            message = kwargs['message']
            del kwargs['message']
        except KeyError:
            message = ''

        # Construct the base command.
        cmd = ['svn', 'commit', self.wcpath, '-m', message]

        # Apply any non-value options.
        for arg in args:
            if arg[:1]=='-': cmd.append(arg)
            elif len(arg)==1: cmd.append('-' + arg)
            else: cmd.append('--' + arg)

        # Apply any valued options.
        for option in sorted(kwargs.keys()):
            if len(option)==1: cmd.append('-' + option)
            else: cmd.append('--' + option)
            cmd.append(str(kwargs[option]))

        # Start the command. Wait for it to finish. A hook failure
        # should run the commit command, but return a non-zero exit
        # code. Details should be provided via the STDERR pipe.
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        return p

    def updateWc(self):
        """Update the entire working copy.

        Returns: Output produced by Subversion command.
        """
        return subprocess.check_output(['svn', 'update', self.wcpath])

    def lockWcPath(self, pathname, user='user',
                   comment=None, force=False):
        """Apply a working copy lock.

        Args:
            pathname: Relative path to be locked.
            user: User requesting the lock.
            comment: Comment associated with lock.
            force: Steal lock from other user.

        Returns: Completed Subversion command process.
        """
        # Get the full path to lock.
        fullpath = os.path.join(self.wcpath, pathname)

        # Construct the lock command.
        cmd = ['svn', 'lock', fullpath, '--username', user]
        if comment != None: cmd += ['--comment', comment]
        if force: cmd += ['--force']

        # Execute the command. Wait for it to finish.
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False)
        p.wait()
        return p

    def unlockWcPath(self, pathname, user='user', force=False):
        """Remove a working copy lock.

        Args:
            pathname: Relative path to be locked.
            user: User requesting the lock.
            force: Break lock of other user.

        Returns: Completed Subversion command process.
        """
        # Get the full path to unlock.
        fullpath = os.path.join(self.wcpath, pathname)

        # Construct the unlock command.
        cmd = ['svn', 'unlock', fullpath, '--username', user]
        if force: cmd += ['--force']

        # Execute the command. Wait for it to finish.
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False)
        p.wait()
        return p

    def makeWcFile(self, pathname, content=''):
        """Create/Replace a working copy file.

        Args:
            pathname: Relative path name of the file.
            content: Content of the file.
        """
        fullpath = os.path.join(self.wcpath, pathname)

        # Create any intermediate folders.
        filedir = os.path.dirname(fullpath)
        if not os.path.isdir(filedir): os.makedirs(filedir)

        # Create/update the file.
        with open(fullpath, 'w') as f:
            f.write(content)

    def makeWcFolder(self, pathname):
        """Create/Replace a working copy folder.

        Args:
            pathname: Relative path name of the folder.
        """
        fullpath = os.path.join(self.wcpath, pathname)
        if os.path.isdir(fullpath): rmtree(fullpath)
        os.makedirs(fullpath)

    def addWcFile(self, pathname, content=''):
        """Create a working copy file and add it.

        Args:
            pathname: Relative path name of the file.
            content: Content of the file.

        Returns: Output produced by Subversion command.
        """
        self.makeWcFile(pathname, content)
        return self.addWcItem(pathname)

    def addWcFolder(self, pathname):
        """Create a working copy folder and add it.

        Args:
            pathname: Relative path name of the folder.

        Returns: Output produced by Subversion command.
        """
        self.makeWcFolder(pathname)
        return self.addWcItem(pathname)

class SmtpTestCase(HookTestCase):
    """SvnHook Test Case with SMTP Server"""

    def setUp(self, repoid, host='localhost', port=8025,
              *args, **kwargs):
        # Initialize the base test case.
        super(SmtpTestCase, self).setUp(repoid, *args, **kwargs)

        # Construct the SMTP server.
        self.smtphost = host
        self.smtpport = port
        self.smtpserver = SmtpSink(host=host, port=port)

        # Start the SMTP server thread.
        self.smtpserver.start()

        # Make sure the SMTP server is always shut down.
        self.addCleanup(self.__class__._stopSmtpServer, self)

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

    def getMessage(self, subject):
        """Get the first email message with a matching subject line.
        Throws a KeyError, when a matching message not found.

        Args:
            subject: Subject line of message.

        Returns: Message object for the matching message.
        """
        # Look at the received message subject lines.
        for msgsubject in [
            message.get('Subject') for message in self.getMailbox()]:
            if msgsubject == subject: return message

        # A matching message wasn't found.
        raise KeyError('Message with subject not found: ' + subject)

    def assertFromAddress(self, message, fromaddr, msg=None):
        """Assert that a message has proper From address.

        Args:
            message: Message to be checked.
            fromaddr: Expected sender email address.
            msg: Optional message to use on failure.
        """
        self.assertEquals(message.get('From'), fromaddr, msg)

    def assertToAddress(self, message, toaddr, msg=None):
        """Assert that a message has proper To address.

        Args:
            message: Message to be checked.
            toaddr: Expected recipient email address.
            msg: Optional message to use on failure.
        """
        self.assertIn(toaddr, message.get_all('To'), msg)

    def assertBody(self, message, body, msg=None):
        """Assert that a message has the correct body.

        Args:
            message: Message to be checked.
            body: Expected body of the email message.
            msg: Optional message to use on failure.
        """
        # Assert against the decoded, non-multipart, content. Trim off
        # the terminal whitespace (two linefeeds).
        self.assertEquals(
            message.get_payload(None, True).rstrip(),
            body.rstrip(), msg)

    def assertBodyRegexp(self, message, regexp, msg=None):
        """Assert that a message body matches a regular expression.

        Args:
            message: Message to be checked.
            regexp: Regular expression to match against the message
              body.
            msg: Optional message to use on failure.
        """
        # Assert against the decoded, non-multipart, content. Trim off
        # the terminal whitespace (two linefeeds).
        self.assertRegexpMatches(
            message.get_payload(None, True).rstrip(), regexp, msg)

    def assertBodyNotRegexp(self, message, regexp, msg=None):
        """Assert that a message body doesn't match a regular
        expression.

        Args:
            message: Message to be checked.
            regexp: Regular expression to match against the message
              body.
            msg: Optional message to use on failure.
        """
        # Assert against the decoded, non-multipart, content. Trim off
        # the terminal whitespace (two linefeeds).
        self.assertNotRegexpMatches(
            message.get_payload(None, True).rstrip(), regexp, msg)

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
