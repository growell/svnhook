"""Action Context Classes"""
__version__ = '3.00'
__all__     = ['CtxStandard', 'CtxRevision', 'CtxTransaction', 'Tokens']

import logging
import re
import shlex, subprocess

logger = logging.getLogger()

class Context(object):
    """Base Class for Hook Context"""

    def __init__(self, tokens):
        """Create a tag context.

        Args:
          tokens: Set of base tokens.
        """
        # Create a deep copy of the tokens.
        self.tokens = Tokens(tokens)

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
                'text = "{0}", tokens = {1}'.format(text, self.tokens))

        # Get the case-insensitive tokens, and their values, as found
        # in the template. This removes any duplicates and ignores any
        # unknown tokens.
        found = Tokens()
        for match in re.finditer(r'\$\{(\w+)\}', text):
            token = match.group(1)
            if token not in found:
                try:
                    found[token] = self.tokens[token]
                except KeyError:
                    continue

        # When no replacements need to be made, stop recursion and
        # pass back the fully-expanded template.
        if len(found) == 0: return text

        # Replace all instances of the tokens.
        for token, value in found.items():
            text = re.sub(
                r'(?i)\$\{' + token + r'\}', str(value), text)

        # Try another level of expansion.
        return self.expand(text, depth + 1)

    def execute(self, cmd):
        """Execute a system call.

        Args:
          cmd: Command and arguments to execute.

        Returns: Output produced by the command.
        """
        cmd = [str(field) for field in cmd]
        logger.debug('Execute: {0}'.format(cmd))
        try:
            p = subprocess.Popen(cmd,
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
            msg = 'Command failed: {0}: {1}'.format(cmd, errstr)
            logger.error(msg)
            raise RuntimeError(msg)

        # Return the STDOUT content.
        return p.stdout.read().strip()

    def get_author(self, options=[]):
        """Get the author of repository changes.

        Args:
          options: Svnlook command options.

        Returns: Output produced by the command.
        """
        # If available, use the cached author.
        if hasattr(self, 'author'): return self.author

        # Get the change author.
        self.author = self.execute(
            ['svnlook', 'author', self.repospath] + options)

        # Return the cached result.
        return self.author

    def get_changes(self, options=[]):
        """Get the list of repository changes.

        Args:
          options: Svnlook command options.

        Returns: Output produced by the command.
        """
        # If available, use the cached list of changes.
        if hasattr(self, 'changes'): return self.changes

        # Track the items added and deleted.
        addpaths = dict()
        deletepaths = dict()

        # Parse the change listing output.
        self.changes = []
        for chgline in self.execute(
            ['svnlook', 'changed', self.repospath]
            + options).splitlines():

            # Construct the change item instance.
            item = ChangeItem(chgline)

            # Add the change item to the list of changes.
            self.changes.append(item)

            # Track the added and deleted items.
            if item.is_add(): addpaths[item.path] = item
            if item.is_delete(): deletepaths[item.path] = item

            # If the path shows in both lists, it's a replacement.
            if item.path in addpaths and item.path in deletepaths:
                addpaths[item.path].replaced = True
                deletepaths[item.path].replaced = True

        # Return the cached list.
        return self.changes

    def get_file_content(self, path, options=[]):
        """Get the content of a repository file.

        Args:
            path: Repository path name of file.

        Returns: Content of the repository file.
        """
        # To limit memory consumption, the file is always retrieved
        # from the repository.
        return self.execute(
            ['svnlook', 'cat', self.repospath, path] + options)

    def get_log_message(self, options=[]):
        """Get the log message of a repository change.

        Args:
          options: Svnlook command options.

        Returns: Output produced by the command.
        """
        # If available, use the cached log message.
        if hasattr(self, 'logmsg'): return self.logmsg

        # Get the change log message.
        self.logmsg = self.execute(
            ['svnlook', 'log', self.repospath] + options)

        # Return the cached result.
        return self.logmsg

    def get_properties(self, path, options=[]):
        """Get the properties of a repository path.

        Args:
            path: Relative repository path name.
            options: Svnlook command options.

        Returns: Dictionary of repository path properties.
        """
        # Return previously cached results for the path. Otherwise,
        # create a path-keyed property cache.
        if hasattr(self, 'properties'):
            if path in self.properties: return self.properties[path]
        else:
            self.properties = dict()
        properties = self.properties[path] = dict()

        # Get the list of path property names.
        for name in self.execute(
            ['svnlook', 'proplist', self.repospath, path]
            + options).splitlines():

            # Remove leading whitespace.
            name = name.lstrip()

            # Get the property value.
            value = self.execute(
                ['svnlook', 'propget', self.repospath, name, path]
                + options)

            # Cache the property.
            properties[name] = value

        # Pass back the path-specific properties.
        return properties

class CtxStandard(Context):
    """Context for Hooks without Revision or Transaction"""

    def get_author(self):
        """Get the author of the last revision.

        Returns: User name of the revision author.
        """
        return super(CtxStandard, self).get_author()

    def get_changes(self):
        """Get the list of changes in the last revision.

        Returns: List of change objects for the changes.
        """
        return super(CtxStandard, self).get_changes()

    def get_file_content(self, path):
        """Get the content of a file in the last revision.

        Args:
            path: Repository path name of file.

        Returns: Content of the revision file.
        """
        return super(CtxStandard, self).get_file_content(path)

    def get_log_message(self):
        """Get the log message of the last revision.

        Returns: Log message of the revision.
        """
        return super(CtxStandard, self).get_log_message()

    def get_properties(self, path):
        """Get the properties of a repository path.

        Args:
            path: Relative repository path name.

        Returns: Dictionary of repository path properties.
        """
        return super(CtxStandard, self).get_properties(path)

class CtxRevision(Context):
    """Context for Hooks with a Revision"""

    def __init__(self, tokens):
        super(CtxRevision, self).__init__(tokens)
        self.revision = tokens['Revision']

    def get_author(self):
        """Get the author of the revision.

        Returns: User name of the revision author.
        """
        return super(CtxRevision, self).get_author(
            ['-r', self.revision])

    def get_changes(self):
        """Get the list of changes in the revision.

        Returns: List of change objects for the changes.
        """
        return super(CtxRevision, self).get_changes(
            ['-r', self.revision])

    def get_file_content(self, path):
        """Get the content of a file in the revision.

        Args:
            path: Repository path name of file.

        Returns: Content of the revision file.
        """
        return super(CtxRevision, self).get_file_content(
            path, ['-r', self.revision])

    def get_log_message(self):
        """Get the log message of the revision.

        Returns: Log message of the revision.
        """
        return super(CtxRevision, self).get_log_message(
            ['-r', self.revision])

    def get_log(self, verbose=False):
        """Get the formatted log entry for the revision.

        Args:
          verbose: Flag requesting changed path info.

        Returns: Log information for the revision.
        """
        cmd = ['svn', 'log', self.reposurl,
               '-r', self.revision]
        if verbose: cmd += ['--verbose']
        return super(CtxRevision, self).execute(cmd)

    def get_properties(self, path):
        """Get the properties of a repository path.

        Args:
            path: Relative repository path name.

        Returns: Dictionary of repository path properties.
        """
        return super(CtxRevision, self).get_properties(
            path, ['-r', self.revision])

class CtxTransaction(Context):
    """Context for Hooks with a Transaction"""

    def __init__(self, tokens):
        super(CtxTransaction, self).__init__(tokens)
        self.transaction = tokens['Transaction']

    def get_author(self):
        """Get the author of the transaction.

        Returns: User name of the transaction author.
        """
        return super(CtxTransaction, self).get_author(
            ['-t', self.transaction])

    def get_changes(self):
        """Get the list of changes in the transaction.

        Returns: List of change objects for the changes.
        """
        return super(CtxTransaction, self).get_changes(
            ['-t', self.transaction])

    def get_file_content(self, path):
        """Get the content of a file in the transaction.

        Args:
            path: Repository path name of file.

        Returns: Content of the transaction file.
        """
        return super(CtxTransaction, self).get_file_content(
            path, ['-t', self.transaction])

    def get_log_message(self):
        """Get the log message of the transaction.

        Returns: Log message of the transaction.
        """
        return super(CtxTransaction, self).get_log_message(
            ['-t', self.transaction])

    def get_properties(self, path):
        """Get the properties of a repository path.

        Args:
            path: Relative repository path name.

        Returns: Dictionary of repository path properties.
        """
        return super(CtxTransaction, self).get_properties(
            path, ['-t', self.transaction])

class Tokens(dict):
    """Dictionary with Case-Insensitive Keys"""

    def __init__(self, data=None):
        super(Tokens, self).__init__()
        if data:
            for key, value in data.items(): self[key] = value
        
    def __setitem__(self, key, value):
        super(Tokens, self).__setitem__(key.upper(), value)

    def __getitem__(self, key):
        return super(Tokens, self).__getitem__(key.upper())

    def __delitem__(self, key):
        super(Tokens, self).__delitem__(key.upper())

    def __contains__(self, key):
        return super(Tokens, self).__contains__(key.upper())

class ChangeItem(object):
    """Change Listing Item Class

    Use the first "svnlook change" line to determine how to separate
    the change flags from the change path. Subsequent change lines are
    parsed using the previously-determined format.
    """

    def __init__(self, chgline):
        """Parse a change line.

        Args:
            chgline: Svnlook line to parse.
        """
        # If the delimiter index isn't known, figure it out. Scan the
        # characters of the first change line.
        if not hasattr(self, 'delimidx'):
            self.delimidx = state = 0
            for chgchar in chgline:

                # Look for the first non-space character.
                if state == 0 and chgchar != ' ': state = 1

                # Look for the next space character.
                elif state == 1 and chgchar == ' ': state = 2

                # Look for the first path character.
                elif state == 2 and chgchar != ' ': break
                
                # Increment the delimiter position.
                self.delimidx += 1

        # Parse the change line.
        self.type = chgline[:self.delimidx - 1]
        self.path = chgline[self.delimidx:]

        # Initialize the replaced path flag.
        self.replaced = False

    def is_add(self):
        """Is the change an add operation?"""
        return re.match(r'A', self.type) != None

    def is_delete(self):
        """Is the change a delete operation?"""
        return re.match(r'D', self.type) != None

    def is_update(self):
        """Is the change a content or property update?"""
        return re.search(r'U', self.type) != None

    def is_update_content(self):
        """Is the change a content update?"""
        return re.match(r'U', self.type) != None

    def is_update_property(self):
        """Is the change a property update?"""
        return re.match(r'_U', self.type) != None

    def is_update_all(self):
        """Is the change both a content and property update?"""
        return re.match(r'UU', self.type) != None

########################### end of file ##############################
