"""Configuration Action Context Classes"""
__version__ = '3.00'
__all__     = ['CtxStandard', 'CtxRevision', 'CtxTransaction']

from changeitem import ChangeItem

import logging
import shlex, subprocess

from string import Template

logger = logging.getLogger()

class Context(object):
    """Base class for hook configuration actions."""

    def __init__(self, tokens):
        """Create a tag context.

        Arguments:
        tokens -- Dictionary of base tokens.

        """
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

    def get_author(self, cmdline):
        """Get the author of repository changes.

        Arguments:
        cmdline -- Svnlook command to acquire author name.

        """
        # When first requested, cache the author name.
        if 'Author' not in self.tokens:
            self.tokens['Author'] = self.execute(cmdline)

        # Return the cached result.
        logger.debug('Author = "{}"'.format(self.tokens['Author']))
        return self.tokens['Author']

    def get_changes(self, cmdline):
        """Get the list of repository changes.

        Arguments:
        cmdline -- Svnlook command to acquire change listing.

        """
        # When first requested, cache the list of changes.
        if 'Changes' not in self.tokens:

            # Track the items added and deleted.
            addpaths = dict()
            deletepaths = dict()

            # Parse the change listing output.
            self.tokens['Changes'] = []
            for chgline in self.execute(cmdline).splitlines():

                # Construct the change item instance.
                item = ChangeItem(chgline)

                # Add the change item to the list of changes.
                self.tokens['Changes'].append(item)

                # Track the added and deleted items.
                if item.is_add(): addpaths[item.path] = item
                if item.is_delete(): deletepaths[item.path] = item

                # If the path shows in both lists, it's a replacement.
                if item.path in addpaths and item.path in deletepaths:
                    addpaths[item.path].replaced = True
                    deletepaths[item.path].replaced = True

        # Return the cached list.
        return self.tokens['Changes']

    def get_file_content(self, cmdline):
        """Get the contents of a repository file.

        Arguments:
        cmdline -- Svnlook command to acquire file content.

        """
        # To limit memory consumption, the file is always retrieved
        # from the repository.
        return self.execute(cmdline);

    def get_log_message(self, cmdline):
        """Get the log message of a repository change.

        Arguments:
        cmdline -- Svnlook command to acquire log message.

        """
        # When first requested, cache the log message.
        if 'LogMsg' not in self.tokens:
            self.tokens['LogMsg'] = self.execute(cmdline)

        # Return the cached result.
        logger.debug('LogMsg = "{}"'.format(self.tokens['LogMsg']))
        return self.tokens['LogMsg']

class CtxStandard(Context):
    """Context class for hooks without revision or transaction."""

    def get_author(self):
        """Get the author of the last revision.

        Returns:
        author -- User name of the revision author.

        """
        return super(CtxStandard, self).get_author(
            'svnlook author "{}"'.format(self.tokens['ReposPath']))

    def get_changes(self):
        """Get the list of changes in the last revision.

        Returns:
        changes -- List of change objects for the changes.

        """
        return super(CtxStandard, self).get_changes(
            'svnlook changes "{}"'.format(self.tokens['ReposPath']))

    def get_file_content(self):
        """Get the content of a file in the last revision.

        Returns:
        content -- Content of the revision file.

        """
        return super(CtxStandard, self).get_file_content(
            'svnlook cat "{}" "{}"'.format(
                self.tokens['ReposPath'],
                self.tokens['Path']))

    def get_log_message(self):
        """Get the log message of the last revision.

        Returns:
        logmsg -- Log message of the revision.

        """
        return super(CtxStandard, self).get_log_message(
            'svnlook log "{}"'.format(self.tokens['ReposPath']))

class CtxRevision(Context):
    """Context class for hooks with a revision."""

    def get_author(self):
        """Get the author of the revision.

        Returns:
        author -- User name of the revision author.

        """
        return super(CtxRevision, self).get_author(
            'svnlook author -r {} "{}"'.format(
                self.tokens['Revision'],
                self.tokens['ReposPath']))

    def get_changes(self):
        """Get the list of changes in the revision.

        Returns:
        changes -- List of change objects for the changes.

        """
        return super(CtxRevision, self).get_changes(
            'svnlook changes -r {} "{}"'.format(
                self.tokens['Revision'],
                self.tokens['ReposPath']))

    def get_file_content(self):
        """Get the content of a file in the revision.

        Returns:
        content -- Content of the revision file.

        """
        return super(CtxRevision, self).get_file_content(
            'svnlook cat -r {} "{}" "{}"'.format(
                self.tokens['Revision'],
                self.tokens['ReposPath'],
                self.tokens['Path']))

    def get_log_message(self):
        """Get the log message of the revision.

        Returns:
        logmsg -- Log message of the revision.

        """
        return super(CtxRevision, self).get_log_message(
            'svnlook log -r {} "{}"'.format(
                self.tokens['Revision'],
                self.tokens['ReposPath']))

class CtxTransaction(Context):
    """Context class for hooks with a transaction."""

    def get_author(self):
        """Get the author of the transaction.

        Returns:
        author -- User name of the transaction author.

        """
        return super(CtxTransaction, self).get_author(
            'svnlook author -t "{}" "{}"'.format(
                self.tokens['Transaction'],
                self.tokens['ReposPath']))

    def get_changes(self):
        """Get the list of changes in the transaction.

        Returns:
        changes -- List of change objects for the changes.

        """
        return super(CtxTransaction, self).get_changes(
            'svnlook changes -t "{}" "{}"'.format(
                self.tokens['Transaction'],
                self.tokens['ReposPath']))

    def get_file_content(self):
        """Get the content of a file in the transaction.

        Returns:
        content -- Content of the transaction file.

        """
        return super(CtxTransaction, self).get_file_content(
            'svnlook cat -t "{}" "{}" "{}"'.format(
                self.tokens['Transaction'],
                self.tokens['ReposPath'],
                self.tokens['Path']))

    def get_log_message(self):
        """Get the log message of the transaction.

        Returns:
        logmsg -- Log message of the transaction.

        """
        return super(CtxTransaction, self).get_log_message(
            'svnlook log -t "{}" "{}"'.format(
                self.tokens['Transaction'],
                self.tokens['ReposPath']))

########################### end of file ##############################
