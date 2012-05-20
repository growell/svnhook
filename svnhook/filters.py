"""Subversion Hook Filter Classes

Run child actions and sub-filters based on filtering conditions.
"""
__version__ = '3.00'
__all__     = ['Filter']

import actions
from regextag import RegexTag

import inspect
import logging
import re
import sys

logger = logging.getLogger()

# Define modules containing action handler classes.
actionmodules = [actions, sys.modules[__name__]]

class Filter(actions.Action):
    """Filter Base Class

    Also used to process root hook actions.
    """

    def run(self):
        """Execute child actions.

        Stop if a child action indicates a non-zero exit code.

        Returns:
        Current exit code of the filter.

        """
        # Execute the child actions.
        exitcode = 0
        for childtag in self.thistag.iterfind(r'./*'):
            logger.debug('child tag = "{}"'.format(childtag.tag))

            # Look for an action handler class that matches the
            # child tag name.
            action = None
            for module in actionmodules:
                try:
                    action = getattr(module, childtag.tag)
                    break
                except AttributeError:
                    continue

            # Ignore non-action (parameter) tags.
            if not action: continue

            # Construct and run the child action.
            logger.debug('Running "{}"...'.format(childtag.tag))
            try:
                exitcode = action(self.context, childtag).run()
            except Exception as e:
                logger.exception(e)
                sys.stderr.write('Internal hook error.'
                                 + ' Please notify administrator.')
                return -1

            # If the child action generated a non-zero exit code, stop
            # processing child actions.

            if exitcode != 0: break

        # Return the current exit code.
        return exitcode

class FilterAuthor(Filter):
    """Author Name Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterAuthor, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('AuthorRegex')
        if regextag == None:
            raise ValueError('Required tag missing: AuthorRegex')
        self.regex = RegexTag(regextag, re.IGNORECASE)

    def run(self):
        """If author conditions match, run child actions.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the author name.
        author = self.context.get_author()
        logger.debug('Author = "{}"'.format(author))

        # If the author doesn't match don't do anything.
        if not self.regex.search(author): return 0

        # Execute the child actions.
        self.context.tokens['Author'] = author
        return super(FilterAuthor, self).run()

class FilterCapabilities(Filter):
    """Client Capabilities Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterCapabilities, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('CapabilitiesRegex')
        if regextag == None:
            raise ValueError(
                'Required tag missing: CapabilitiesRegex')
        self.regex = RegexTag(regextag)

    def run(self):
        """If client capabilities match, run actions.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the capabilities string.
        capabilities = self.context.tokens['Capabilities']
        logger.debug('Capabilities = "{}"'.format(capabilities))

        # If the capabilities don't match, do nothing.
        if not self.regex.match(capabilities): return 0

        # Perform the child actions.
        self.context.tokens['Capabilities'] = capabilities
        return super(FilterCapabilities, self).run()

class FilterChanges(Filter):
    """Change List Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterChanges, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator for the path
        # names.
        pathregextag = self.thistag.find('ChgPathRegex')
        if pathregextag != None:
            self.pathregex = RegexTag(pathregextag)
        else:
            self.pathregex = None

        # Construct a regular expression tag evaluator for the change
        # types.
        typeregextag = self.thistag.find('ChgTypeRegex')
        if typeregextag != None:
            self.typeregex = RegexTag(typeregextag)
        else:
            self.typeregex = None

        # Require at least one regex tag.
        if typeregex == None and pathregex == None:
            raise ValueError(
                'Required tag missing: ChgPathRegex or ChgTypeRegex')

    def run(self):
        """Filter actions based on changes.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the dictionary of changes.
        changes = self.context.get_changes()

        # Compare the changes to the regular expressions.
        ismatch = False
        for [chgpath, chgtype] in changes:
            logger.debug('ChgPath = "{}"'.format(chgpath))
            logger.debug('ChgType = "{}"'.format(chgtype))

            # Check for a change path mismatch.
            if self.pathregex and not pathregex.search(chgpath):
                continue

            # Check for a change type mismatch.
            if self.typeregex and not typeregex.match(chgtype):
                continue

            # Save the triggering change details.
            self.context.tokens['ChgPath'] = chgpath
            self.context.tokens['ChgType'] = chgtype

            # Indicate that the child action should be run and stop
            # checking.
            ismatch = True
            break

        # If nothing matched, don't do anything.
        if not ismatch: return 0

        # Execute the child actions.
        return super(FilterChanges, self).run()

class FilterLockTokens(Filter):
    """Lock Token Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterLockTokens, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator for the names.
        nameregextag = self.thistag.find('LockNameRegex')
        if nameregextag != None:
            self.nameregex = RegexTag(nameregextag)
        else:
            self.nameregex = None

        # Construct a regular expression tag evaluator for the paths.
        pathregextag = self.thistag.find('LockPathRegex')
        if pathregextag != None:
            self.pathregex = RegexTag(pathregextag)
        else:
            self.pathregex = None

        # Require at least one regex tag.
        if nameregex == None and pathregex == None:
            raise ValueError('Required tag missing:'
                             + ' LockNameRegex or LockPathRegex')

    def run(self):
        """Filter actions based on lock tokens.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the dictionary of changes.
        changes = self.context.get_changes()

        # Compare the changes to the regular expressions.
        ismatch = False
        for locktoken in self.context.tokens['LockTokens']:
            [lockname, lockpath] = locktoken.split(r'\|')
            logger.debug('LockName = "{}"'.format(lockname))
            logger.debug('LockPath = "{}"'.format(lockpath))

            # Check for a lock name mismatch.
            if self.nameregex and not nameregex.match(lockname):
                continue

            # Check for a lock path mismatch.
            if self.pathregex and not pathregex.search(lockpath):
                continue

            # Save the triggering change details.
            self.context.tokens['LockName'] = lockname
            self.context.tokens['LockPath'] = lockpath

            # Indicate that the child action should be run and stop
            # checking.
            ismatch = True
            break

        # If nothing matched, don't do anything.
        if not ismatch: return 0

        # Execute the child actions.
        return super(FilterLockTokens, self).run()

class FilterLogMsg(Filter):
    """Log Message Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterLogMsg, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('LogMsgRegex')
        if regextag == None:
            raise ValueError('Required tag missing: LogMsgRegex')
        self.regex = RegexTag(regextag)

    def run(self):
        """Filter actions based on log message.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the current log message.
        logmsg = self.context.get_log_message()

        # If the log message doesn't match, don't do anything.
        if not self.regex.search(logmsg): return 0

        # Execute the child actions.
        self.context.tokens['LogMsg'] = logmsg
        return super(FilterLogMsg, self).run()

class FilterPath(Filter):
    """Single Path Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterPath, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('PathRegex')
        if regextag == None:
            raise ValueError('Required tag missing: PathRegex')
        self.regex = RegexTag(regextag)

    def run(self):
        """Filter operations based on current path name.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the path name.
        path = self.context.tokens['Path']
        logger.debug('Path = "{}"'.format(path))

        # If the path name doesn't match, do nothing.
        if not self.regex.search(path): return

        # Execute the child actions.
        return super(FilterPath, self).run()

class FilterUser(Filter):
    """User Name Filter Class"""

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterUser, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('UserRegex')
        if regextag == None:
            raise ValueError('Required tag missing: UserRegex')
        self.regex = RegexTag(regextag)

    def run(self):
        """Filter operations based on user name.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the user name.
        user = self.context.tokens['User']
        logger.debug('User = "{}"'.format(user))

        # If the user name doesn't match, do nothing.
        if not self.regex.search(user): return

        # Execute the child actions.
        return super(FilterUser, self).run()

########################### end of file ##############################
