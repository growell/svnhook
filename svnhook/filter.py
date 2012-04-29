"""Subversion Hook Filter Classes

Run child actions and sub-filters based on filtering conditions.
"""
__version__ = '3.00'
__all__     = ['Filter']

import action
from regextag import RegexTag

import inspect
import logging
import re
import sys

logger = logging.getLogger()

# Define modules containing action handler classes.
actionmodules = [action, sys.modules[__name__]]

class Filter(action.Action):
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
                logger.critical(e)
                sys.stderr.write('Internal hook error.'
                                 + ' Please notify administrator.')
                return -1

            # If the child action generated a non-zero exit code, stop
            # processing child actions.

            if exitcode != 0: break

        # Return the current exit code.
        return exitcode

class FilterAuthor(Filter):

    def run(self):
        """If author conditions match, run child actions.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('AuthorRegex')
        if regextag == None:
            raise ValueError('Required tag missing: AuthorRegex')
        regex = RegexTag(regextag, re.IGNORECASE)

        # Get the author name.
        author = self.context.get_author()
        logger.debug('Author = "{}"'.format(author))

        # If the author doesn't match don't do anything.
        if not regex.search(author): return 0

        # Execute the child actions.
        return super(FilterAuthor, self).run()

class FilterCapabilities(Filter):

    def run(self):
        """If client capabilities match, run actions.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('CapabilitiesRegex')
        if regextag==None:
            raise ValueError(
                'Required tag missing: CapabilitiesRegex')
        regex = RegexTag(regextag)

        # Get the capabilities string.
        capabilities = self.context.tokens['Capabilities']
        logger.debug('Capabilities = "{}"'.format(capabilities))

        # If the capabilities don't match, do nothing.
        if not regex.match(capabilities): return 0

        # Perform the child actions.
        return super(FilterCapabilities, self).run()

class FilterChanges(Filter):

    def run(self):
        """Filter actions based on changes.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the change path regex.
        pathregextag = self.thistag.find('ChgPathRegex')
        if pathregextag == None:
            pathregex = None
        else:
            pathregex = RegexTag(pathregextag)

        # Get the change type regex.
        typeregextag = self.thistag.find('ChgTypeRegex')
        if typeregextag == None:
            typeregex = None
        else:
            typeregex = RegexTag(typeregextag, re.IGNORECASE)

        # Require at least one regex tag.
        if typeregex == None and pathregex == None:
            raise ValueError(
                'Required tag missing: ChgPathRegex or ChgTypeRegex')

        # Get the dictionary of changes.
        changes = self.context.get_changes()

        # Compare the changes to the regular expressions.
        ismatch = False
        for [chgpath, chgtype] in changes:
            logger.debug('ChgPath = "{}"'.format(chgpath))
            logger.debug('ChgType = "{}"'.format(chgtype))

            # Check for a change path mismatch.
            if pathregex and not pathregex.search(chgpath): continue

            # Check for a change type mismatch.
            if typeregex and not typeregex.match(chgtype): continue

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

class FilterLogMsg(Filter):

    def run(self):
        """Filter actions based on log message.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the log message regex tag.
        regextag = self.thistag.find('LogMsgRegex')
        if regextag == None:
            raise ValueError('Required tag missing: LogMsgRegex')
        regex = RegexTag(regextag)

        # Get the current log message.
        logmsg = self.context.get_log_message()

        # If the log message doesn't match, don't do anything.
        if not regex.search(logmsg): return 0

        # Execute the child actions.
        return super(FilterLogMsg, self).run()

class FilterUser(Filter):

    def run(self):
        """Filter operations based on user name.

        Returns:
        Exit code produced by filter and child actions.

        """
        # Get the user name regex tag.
        regextag = self.thistag.find('UserRegex')
        if regextag == None:
            raise ValueError('Required tag missing: UserRegex')
        regex = RegexTag(regextag, re.IGNORECASE)

        # Get the user name.
        user = self.context.tokens['User']
        logger.debug('User = "{}"'.format(user))

        # If the user name doesn't match, do nothing.
        if not regex.search(user): return

        # Execute the child actions.
        return super(FilterUser, self).run()

########################### end of file ##############################
