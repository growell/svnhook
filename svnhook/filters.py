"""Subversion Hook Filter Classes

Run child actions and sub-filters based on filtering conditions.
"""
__version__ = '3.00'
__all__     = ['Filter']

import actions

import inspect
import logging
import re
import sys, subprocess, shlex, errno

logger = logging.getLogger()

# Define modules containing action handler classes.
actionmodules = [actions, sys.modules[__name__]]

class Filter(actions.Action):
    """Filter Base Class

    Also used to process root hook actions.
    """

    def run(self):
        """Execute child actions, until one of them sets a non-zero
        exit code.

        Returns: Exit code of the filter.
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

class FilterAddNameCase(Filter):
    """Added Entries Name Case Filter Class

    Look for added (not replaced) entries whose names differ only by
    case with existing entries. Most often used to avoid problems with
    checkouts on case-insensitive (i.e. Windows) operating systems.

    Applies To: pre-commit
    Input Tokens: ReposPath, Transaction
    Output Tokens: ParentFolder, AddedName, ExistingName
    """

    def __init__(self, *args, **kwargs):
        # Construct the base instance.
        super(FilterAddNameCase, self).__init__(*args, **kwargs)

        # Initialize the repository listing cache.
        self.listings = dict();

    def get_listing(self, folder):
        """Get the existing entries in a repository folder.

        Args:
          folder: Path name of the repository folder.

        Returns: Map of uppercased existing folder entry names
        versus original folder entry names.
        """
        # If the listing was previously produced, return it.
        if folder in self.listings: return self.listings[folder]

        # This is a new folder. Start with an empty list.
        listing = self.listings[folder] = dict()

        # Request the parent folder listing.
        cmdline = 'svnlook tree "{}" "{}" --non-recursive'\
            .format(self.context.repospath, folder)
        logger.debug('Execute: ' + cmdline)
        try:
            p = subprocess.Popen(
                shlex.split(cmdline),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)

        # If unable to execute, complain.
        except Exception as e:
            logger.error(e)
            raise e

        # The process started, wait for it to finish.
        p.wait()

        # The parent folder may be added, as part of this
        # revision. Treat the "file not found" error as
        # returning an empty listing - so we don't ask for it
        # again.
        if p.returncode == errno.ENOENT: return listing
        elif p.returncode != 0:
            errstr = p.stderr.read().strip()
            msg = 'Command failed: {}: {}'.format(cmdline, errstr)
            logger.error(msg)
            raise RuntimeError(msg)

        # Parse the folder listing.
        for line in p.stdout.readlines():
            logger.debug('line = "{}"'.format(line.rstrip()))

            # Skip blank lines and headers.
            match = re.match(r'\s((\S+?)/?)$', line.rstrip())
            if match == None: continue

            # Add the entry to the listing.
            name, value = match.group(2,1)
            listing[name.upper()] = value

        return listing

    def run(self):
        """Look for a name case conflict.

        Returns: Exit code from filter and child actions.
        """
        # Look for a match with the changed items.
        matched = False
        for change in self.context.get_changes():

            # Ignore anything that isn't added. Ignore replacements.
            if (not change.is_add()) or change.replaced: continue

            # Determine the parent folder and base name.
            folder, typedname, name = re.match(
                r'(.*/)?((.+?)/?)$', change.path).group(1,2,3)
            if folder == None: folder = '/'
            logger.debug(
                'folder = "{}", typedname = "{}", name = "{}"'\
                    .format(folder, typedname, name))

            # Skip entries not in the case-insensitive listing.
            listing = self.get_listing(folder)
            if name.upper() not in listing: continue

            # Add tokens for the conflict details.
            self.context.tokens['ParentFolder'] = folder
            self.context.tokens['AddedName'] = typedname
            self.context.tokens['ExistingName']\
                = listing[name.upper()]
            matched = True
            break

        # A match wasn't found, don't do the child actions.
        if not matched: return 0

        # Perform the child actions.
        return super(FilterAddNameCase, self).run()

class FilterAuthor(Filter):
    """Author Name Filter Class

    Look for a match with the current commit author.

    Applies To: pre-commit, post-commit
    Input Tags: AuthorRegex
    Output Tokens: Author
    """

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
    """Client Capabilities Filter Class

    Look for a match with the client capabilities.

    Applies To: start-commit
    Input Tokens: Capabilities
    Input Tags: CapabilitiesRegex
    """

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
        if not self.regex.search(capabilities): return 0

        # Perform the child actions.
        return super(FilterCapabilities, self).run()

class FilterChgType(Filter):
    """RevProp Change Type Filter Class

    Look for a revision property change type.

    Applies To: pre-revprop-change, post-revprop-change
    Input Tokens: ChgType
    Input Tags: ChgTypeRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterChgType, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('ChgTypeRegex')
        if regextag == None:
            raise ValueError('Required tag missing: ChgTypeRegex')
        self.regex = RegexTag(regextag)

    def run(self):
        """If revprop change types match, run actions.

        Returns: Exit code produced by filter and child actions.
        """
        # Get the change type string.
        chgtype = self.context.tokens['ChgType']
        logger.debug('ChgType = "{}"'.format(chgtype))

        # If the capabilities don't match, do nothing.
        if not self.regex.match(chgtype): return 0

        # Perform the child actions.
        return super(FilterChgType, self).run()

class FilterCommitList(Filter):
    """Commit List Filter Class

    Look for a match in the list of commit list paths.

    Input tokens: ReposPath, Transaction, Revision
    Input tags: PathRegex, ChgTypeRegex
    Output tokens: Path, ChgType
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""
        # Construct the base instance.
        super(FilterChanges, self).__init__(*args, **kwargs)

        # Save the "stop on first match" flag.
        self.matchfirst = self.get_boolean('matchFirst')
        logger.debug('matchFirst = ' + self.matchfirst)

        # Construct a regular expression tag evaluator for the path
        # names.
        pathregextag = self.thistag.find('PathRegex')
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

        Returns: Exit code produced by filter and child actions.
        """
        # Get the dictionary of changes.
        changes = self.context.get_changes()

        # Compare the changes to the regular expressions.
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
            self.context.tokens['Path'] = chgpath
            self.context.tokens['ChgType'] = chgtype

            # Execute the child actions. If they produce a non-zero
            # exit code, or if only looking for the first match, stop
            # checking.
            exitcode = super(FilterCommitList, self).run()
            if exitcode or self.matchfirst: return exitcode

        # Either nothing matched, or the child actions were
        # successful.
        return 0

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

class RegexTag(object):
    """Regular Expression Tag Class

    Evaluate text against regular expression details provided by a
    hook configuration XML tag.
    """

    def __init__(self, regextag, *args):
        """Construct instance from regular expression tag.

        Args:
          regextag: Element instance for the regex tag.
          *args: Regular expression flags.
        """
        if regextag.text == None:
            raise ValueError(
                'Required tag content missing: {}'.format(regextag.tag))

        # Compile the regular expression.
        self.regex = re.compile(regextag.text, *args)

        # Determine the true/false sense to apply to the result.
        self.sense = (re.match(r'(1|true|yes)$',
                              regextag.get('sense', default='1'),
                              re.IGNORECASE) != None)

    def match(self, text):
        """Compare start of the text to the regular expression.

        Args:
          text: Text to be evaluated.

        Returns: Boolean result of the comparison.
        """
        if self.sense:
            return (self.regex.match(text) != None)
        else:
            return (self.regex.match(text) == None)

    def search(self, text):
        """Compare all of the text to the regular expression.

        Args:
          text: Text to be evaluated.

        Returns: Boolean result of the comparison.
        """
        if self.sense:
            return (self.regex.search(text) != None)
        else:
            return (self.regex.search(text) == None)

########################### end of file ##############################
