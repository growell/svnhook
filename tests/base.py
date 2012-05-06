#!/usr/bin/env python
######################################################################
# SvnHook Test Case Core Classes
######################################################################
__all__ = ['HookTestCase', 'LogFile']

import re
import os, sys, shutil
import subprocess
import unittest

# Define the data root.
datadir = os.path.normpath(os.path.join(
        os.path.dirname(__file__), 'data'))
tmpdir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'tmp'))

# If needed, create the temporary directory.
if not os.path.isdir(tmpdir): os.mkdirs(tmpdir)

class HookTestCase(unittest.TestCase):
    """SvnHook Test Case Base Class"""

    def setUp(self, repoid, username='user', password='password'):
        """Initialize the test repository.

        Arguments:
        repoid -- Identifier for the repository and data set.
        username -- Working copy user name (default=user).
        password -- Working copy password  (default=password).

        """
        self.repoid = repoid
        self.username = username
        self.password = password

        self.repopath = os.path.join(tmpdir, repoid + '-repo')
        self.repourl = 'file://' + self.repopath
        self.wcpath = os.path.join(tmpdir, repoid + '-wc')

        # If the repository already exists, delete it.
        if os.path.isdir(self.repopath): shutil.rmtree(self.repopath)
            
        # If the working copy already exists, delete it.
        if os.path.isdir(self.wcpath): shutil.rmtree(self.wcpath)
            
        # Construct the test repository.
        subprocess.check_call(['svnadmin', 'create', self.repopath])

        # Check for repository initialization data directory.
        repodata = os.path.join(datadir, repoid)
        if os.path.isdir(repodata):

            # Load the initialization files.
            for datafile in os.listdir(repodata):

                # Load a repository dump file.
                if datafile[-4:] == '.dmp':
                    subprocess.check_call(
                        ['svnadmin', 'load', self.repopath],
                        stdin=open(datafile))

                # Load a hook configuration file.
                elif re.match(datafile, r'.*\.(conf|[xy]ml)') != None:
                    shutil.copy(
                        datafile, os.path.join(self.repopath, 'conf'))

                # Load a hook script.
                elif datafile[-3:] == '.sh':
                    hookfile = os.path.join(
                        self.repopath, 'hooks', re.sub(
                            r'\.sh$', '', os.path.basename(datafile)))
                    shutil.copyfile(datafile, hookfile)

        # Create the initial working copy.
        subprocess.check_call(
            ['svn', 'checkout', self.repourl, self.wcpath,
             '--username', self.username,
             '--password', '"{}"'.format(self.password)])

    def writeConf(self, filename, content):
        """Write content into a repository configuration file.

        Arguments:
        filename - File name of the 'conf' directory file.
        content  - Content to store in the file.

        """
        filepath = os.path.join(self.repopath, 'conf', filename)
        with open(filepath, 'w') as f:
            f.write(content)

    def getLogFile(self, filename):
        """Get the scanner object for a log file.

        Arguments:
        filename - File name of the 'logs' directory file.

        Returns:
        Log file scanner object.

        """
        return LogFile(os.path.join(self.repopath, 'logs', filename))

    def addWcItem(self, pathname):
        """Schedule working copy items for addition.

        Arguments:
        pathname -- Relative path name of the item.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(['svn', 'add', fullpath])

    def rmWcItem(self, pathname):
        """Schedule working copy items for deletion.

        Arguments:
        pathname -- Relative path name of the item.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(['svn', 'rm', fullpath])

    def setWcProperty(self, propname, propval, pathname='.'):
        """Set a working copy property.

        Arguments:
        propname -- Name of the property.
        propval -- Value of the property.
        pathname -- Relative path name of target (default='.').

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(
            ['svn', 'propset', propname, propval, fullpath])

    def delWcProperty(self, propname, pathname='.'):
        """Delete a working copy property.

        Arguments:
        propname -- Name of the property.
        pathname -- Relative path name of target (default='.').

        """
        fullpath = os.path.join(self.wcpath, pathname)
        subprocess.check_call(
            ['svn', 'propdel', propname, fullpath])

    def revertWc(self):
        """Revert all working copy changes."""
        subprocess.check_call(['svn', 'revert', self.wcpath, '-R'])

    def commitWc(self, message='', *args, **kwargs):
        """Commit working copy changes.

        Arguments:
        message -- Log message for commit (default='').

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

        Arguments:
        pathname -- Relative path name of the file.
        content -- Content of the file (default='').

        """
        fullpath = os.path.join(self.wcpath, pathname)

        # Create any intermediate folders.
        os.mkdirs(os.path.dirname(fullpath))

        # Create/update the file.
        with open(fullpath, 'w') as f:
            f.write(content)

    def makeWcFolder(self, pathname):
        """Create/Replace a working copy folder.

        Arguments:
        pathname -- Relative path name of the folder.

        """
        fullpath = os.path.join(self.wcpath, pathname)
        if os.isdir(fullpath): os.rmtree(fullpath)
        os.mkdirs(fullpath)

    def addWcFile(self, pathname, content=''):
        """Create a working copy file and add it.

        Arguments:
        pathname -- Relative path name of the file.
        content -- Content of the file (default='').

        """
        self.makeWcFile(pathname, content)
        self.addWcItem(pathname)

    def addWcFolder(self, pathname):
        """Create a working copy folder and add it.

        Arguments:
        pathname -- Relative path name of the folder.

        """
        self.makeWcFolder(pathname)
        self.addWcItem(pathname)

class LogFile(object):
    """SvnHook Log File Scanner"""

    def __init__(self, pathname):
        """Mark the end position of the log file.

        Arguments:
        pathname - Path name of the log file.

        """
        self.pathname = pathname

        # Mark the current EOF.
        with open(pathname) as f:
            f.seek(0, os.SEEK_END)
            self.position = f.tell()

    def read(self):
        """Get the added log file content.

        Returns:
        Lines added to the log file.

        """
        # Get the added content. Update the saved position.
        with open(self.pathname) as f:
            f.seak(self.position, os.SEEK_SET)
            content = f.read()
            self.position = f.tell()

        return content

########################### end of file ##############################
