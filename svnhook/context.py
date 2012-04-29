"""Configuration Action Context Classes"""
__version__ = '3.00'
__all__     = ['CtxStandard', 'CtxRevision', 'CtxTransaction']

from svnhook.changeitem import ChangeItem

import logging
import shlex, subprocess

from string import Template

logger = logging.getLogger(__name__)

class Context(object):
    """Base class for hook configuration actions."""

    def __init__(self, tokens):
        """Create a tag context.

        Arguments:
        tokens -- Dictionary of base tokens.

        """
        # Make sure the local repository path and user name are
        # provided.
        if 'ReposPath' not in tokens:
            raise ValueError('Required token missing: ReposPath')
        if 'User' not in tokens:
            raise ValueError('Required token missing: User')

        # Create a deep copy of the tokens.
        self.tokens = dict(tokens)

    def expand(self, template):
        """Apply tokens to a template string.

        Arguments:
        template -- String containing tokens.

        Returns:
        Template string with token substitutions.

        """
        engine = Template(template)
        return engine.safe_substitute(self.tokens)

    def get_changes(self, chglines):
        """Get a list of change instances.

        Arguments:
        chglines -- Listing data from the "svnlook changed".

        Returns:
        Array of change instances for the changed items.

        """
        changes = []
        paths = dict()
        for chgline in chglines:

            # Construct the change item instance.
            item = ChangeItem(chgline)

            # Add the change item to the list of changes.
            changes.append(item)

            # Track the changed path for replacement detection.
            if item.path not in paths:
                paths[item.path] = dict({ 'add': 0, 'delete': 0 })
            path = paths[item.path]

            # If the item was both added and deleted, it's a
            # replacement.
            if item.isadd(): path['add'] = True
            if item.isdelete(): path['delete'] = True

            item.replaced = path['add'] and path['delete']

        return changes

    def execute(self, cmdline):
        """Execute a system call.

        Arguments:
        cmdline -- Command line to execute.

        Returns:
        Output produced by the command.

        """
        logger.debug('Execute: ' + cmdline)
        try:
            p = subprocess.Popen(shlex.split(cmdline),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=False)
        except Exception as e:
            logger.error(e)
            raise e

        # The process started, wait for it to finish.
        p.wait()

        # Handle errors returned by the command.
        if p.returncode != 0:
            errstr = p.stderr.read().strip()
            msg = 'Command failed: {}: {}'.format(cmdline, errstr)
            logger.error(msg)
            raise RuntimeError(msg)

        # Return the STDOUT content.
        return p.stdout.read().strip()

class CtxStandard(Context):
    """Context class for hooks without revision or transaction."""

    def get_author(self):
        """Get the author of the last revision."""
        # When first requested, cache the last change author.
        if 'Author' not in self.tokens:
            self.tokens['Author'] = self.execute(
                'svnlook author "{}"'.format(
                    self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('Author = "{}"'.format(self.tokens['Author']))
        return self.tokens['Author']

    def get_log_message(self):
        """Get the log message of the last revision."""
        # When first requested, cache the last change message.
        if 'LogMsg' not in self.tokens:
            self.tokens['LogMsg'] = self.execute(
                'svnlook log "{}"'.format(self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('LogMsg = "{}"'.format(self.tokens['LogMsg']))
        return self.tokens['LogMsg']

class CtxRevision(Context):
    """Context class for hooks with a revision."""

    def get_author(self):
        """Get the author of the revision."""
        # When first requested, cache the revision author.
        if 'Author' not in self.tokens:
            self.tokens['Author'] = self.execute(
                'svnlook author -r {} "{}"'.format(
                    self.tokens['Revision'],
                    self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('Author = "{}"'.format(self.tokens['Author']))
        return self.tokens['Author']

    def get_log_message(self):
        """Get the log message of the revision."""
        # When first requested, cache the revision message.
        if 'LogMsg' not in self.tokens:
            self.tokens['LogMsg'] = self.execute(
                'svnlook log -r {} "{}"'.format(
                    self.tokens['Revision'],
                    self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('LogMsg = "{}"'.format(self.tokens['LogMsg']))
        return self.tokens['LogMsg']

class CtxTransaction(Context):
    """Context class for hooks with a transaction."""

    def get_author(self):
        """Get the author of the transaction."""
        # When first requested, cache the transaction author.
        if 'Author' not in self.tokens:
            self.tokens['Author'] = self.execute(
                'svnlook author -t "{}" "{}"'.format(
                    self.tokens['Transaction'],
                    self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('Author = "{}"'.format(self.tokens['Author']))
        return self.tokens['Author']

    def get_log_message(self):
        """Get the log message of the transaction."""
        # When first requested, cache the transaction message.
        if 'LogMsg' not in self.tokens:
            self.tokens['LogMsg'] = self.execute(
                'svnlook log -t "{}" "{}"'.format(
                    self.tokens['Transaction'],
                    self.tokens['ReposPath']))

        # Return the cached result.
        logger.debug('LogMsg = "{}"'.format(self.tokens['LogMsg']))
        return self.tokens['LogMsg']

########################### end of file ##############################
