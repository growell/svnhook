"""Configuration Action Context Classes"""
__version__ = '3.00'
__all__     = ['CtxStandard', 'CtxRevision', 'CtxTransaction']

from changeitem import ChangeItem

import logging
import re
import shlex, subprocess

from string import Template

logger = logging.getLogger()

class Context(object):
    """Base class for hook configuration actions."""

    def __init__(self, tokens):
        """Create a tag context.

        Args:
          tokens: Dictionary of base tokens.
        """
        # Create a deep copy of the tokens.
        self.tokens = dict(tokens)

        # All of the hooks provide this. Simplify access.
        self.repospath = tokens['ReposPath']

        # Transform the repository path into a file protocol URL.
        # This is needed to utilize regular "svn" commands.
        if self.repospath[:1] == '/':
            self.reposurl = 'file://' + self.repospath
        else:
            self.reposurl = 'file:///'\
                + re.sub(r'\\', r'/', self.repospath)

    def expand(self, text, depth=1):
        """Expand tokens found in a string.

        Args:
          text: String that may contain tokens.
          depth: Incremental recursion depth count.

        Returns: String with token replacements.
        """
        # Limit the recursion depth.
        if depth > 12: raise RuntimeError(
            'Maximum token recursion depth exceeded: '\
                'text = "{}", tokens = {}'.format(text, self.tokens))

        # Get the case-insensitive tokens, and their values, as found
        # in the template. This removes any duplicates and ignores any
        # unknown tokens.
        found = dict()
        for match in re.finditer(r'\$\{(\w+)\}', text):
            token = match.group(1).upper()
            if token not in found:
                try:
                    found[token] = self.tokens[token]
                except KeyError:
                    continue

        # When no replacements need to be made, stop recursion and
        # pass back the fully-expanded template.
        if len(found) == 0: return text

        # Replace all instances of the tokens.
        for (token, value) in found.items():
            text = re.sub(r'\$\{' + token + r'\}',
                   value, text, flags=re.IGNORECASE)

        # Try another level of expansion.
        return self.expand(text, depth + 1)

    def execute(self, cmdline):
        """Execute a system call.

        Args:
          cmdline: Command line to execute.

        Returns: Output produced by the command.
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

        Args:
          cmdline: Svnlook command to acquire author name.

        Returns: Output produced by the command.
        """
        # When first requested, cache the author name.
        if 'Author' not in self.tokens:
            self.tokens['Author'] = self.execute(cmdline)

        # Return the cached result.
        logger.debug('Author = "{}"'.format(self.tokens['Author']))
        return self.tokens['Author']

    def get_changes(self, cmdline):
        """Get the list of repository changes.

        Args:
          cmdline: Svnlook command to acquire change listing.

        Returns: Output produced by the command.
        """
        # If available, use the cached list of changes.
        if 'Changes' in self.tokens: return self.tokens['Changes']

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

    def get_log_message(self, cmdline):
        """Get the log message of a repository change.

        Args:
          cmdline: Svnlook command to acquire log message.

        Returns: Output produced by the command.
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

        Returns: User name of the revision author.
        """
        return super(CtxStandard, self).get_author(
            'svnlook author "{}"'.format(self.repospath))

    def get_changes(self):
        """Get the list of changes in the last revision.

        Returns: List of change objects for the changes.
        """
        return super(CtxStandard, self).get_changes(
            'svnlook changed "{}"'.format(self.repospath))

    def get_file_content(self):
        """Get the content of a file in the last revision.

        Returns: Content of the revision file.
        """
        # To limit memory consumption, the file is always retrieved
        # from the repository.
        return super(CtxStandard, self).execute(
            'svnlook cat "{}" "{}"'.format(
                self.repospath,
                self.tokens['Path']))

    def get_log_message(self, verbose=False):
        """Get the log message of the last revision.

        Returns: Log message of the revision.
        """
        return super(CtxStandard, self).get_log_message(
            'svnlook log "{}"'.format(self.repospath))

class CtxRevision(Context):
    """Context class for hooks with a revision."""

    def __init__(self, tokens):
        super(CtxRevision, self).__init__(tokens)
        self.revision = tokens['Revision']

    def get_author(self):
        """Get the author of the revision.

        Returns: User name of the revision author.
        """
        return super(CtxRevision, self).get_author(
            'svnlook author -r {} "{}"'.format(
                self.revision, self.repospath))

    def get_changes(self):
        """Get the list of changes in the revision.

        Returns: List of change objects for the changes.
        """
        return super(CtxRevision, self).get_changes(
            'svnlook changed -r {} "{}"'.format(
                self.revision, self.repospath))

    def get_file_content(self):
        """Get the content of a file in the revision.

        Returns: Content of the revision file.
        """
        # To limit memory consumption, the file is always retrieved
        # from the repository.
        return super(CtxRevision, self).execute(
            'svnlook cat -r {} "{}" "{}"'.format(
                self.revision, self.repospath, self.tokens['Path']))

    def get_log_message(self, verbose=False):
        """Get the log message of the revision.

        Returns: Log message of the revision.
        """
        return super(CtxRevision, self).get_log_message(
            'svnlook log -r {} "{}"'.format(
                self.revision, self.repospath))

    def get_log(self, verbose=False):
        """Get the formatted log entry for the revision.

        Args:
          verbose: Flag requesting changed path info.

        Returns: Log information for the revision.
        """
        if verbose:
            cmdline = 'svn log -r {} {} --verbose'.format(
                self.revision, self.reposurl)
        else:
            cmdline = 'svn log -r {} {}'.format(
                self.revision, self.reposurl)
        return super(CtxRevision, self).execute(cmdline)

class CtxTransaction(Context):
    """Context class for hooks with a transaction."""

    def __init__(self, tokens):
        super(CtxTransaction, self).__init__(tokens)
        self.transaction = tokens['Transaction']

    def get_author(self):
        """Get the author of the transaction.

        Returns: User name of the transaction author.
        """
        return super(CtxTransaction, self).get_author(
            'svnlook author -t "{}" "{}"'.format(
                self.transaction, self.repospath))

    def get_changes(self):
        """Get the list of changes in the transaction.

        Returns: List of change objects for the changes.
        """
        return super(CtxTransaction, self).get_changes(
            'svnlook changed -t "{}" "{}"'.format(
                self.transaction, self.repospath))

    def get_file_content(self):
        """Get the content of a file in the transaction.

        Returns: Content of the transaction file.
        """
        # To limit memory consumption, the file is always retrieved
        # from the repository.
        return super(CtxTransaction, self).execute(
            'svnlook cat -t "{}" "{}" "{}"'.format(
                self.transaction, self.repospath,
                self.tokens['Path']))

    def get_log_message(self, verbose=False):
        """Get the log message of the transaction.

        Returns: Log message of the transaction.
        """
        return super(CtxTransaction, self).get_log_message(
            'svnlook log -t "{}" "{}"'.format(
                self.transaction, self.repospath))

########################### end of file ##############################
