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
        # Get the child element iterator.
        if hasattr(self.thistag, 'iterfind'):
            childiter = self.thistag.iterfind(r'./*')
        else:
            childiter = self.thistag.findall(r'./*')

        # Execute the child actions.
        exitcode = 0
        for childtag in childiter:
            logger.debug('child tag = "{0}"'.format(childtag.tag))

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
            logger.debug('Running "{0}"...'.format(childtag.tag))
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
        cmdline = 'svnlook tree "{0}" "{1}" --non-recursive'\
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
            msg = 'Command failed: {0}: {1}'.format(cmdline, errstr)
            logger.error(msg)
            raise RuntimeError(msg)

        # Parse the folder listing.
        for line in p.stdout.readlines():
            logger.debug('line = "{0}"'.format(line.rstrip()))

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
                'folder = "{0}", typedname = "{1}", name = "{2}"'\
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

    Input Tokens: ReposPath, Transaction or Revision
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

        # Get the author of the transaction or revision. This will
        # cache the author name in the "Author" token.
        self.author = self.context.get_author()
        logger.debug('author = "{0}"'.format(self.author))

    def run(self):
        """If author conditions match, run child actions.

        Returns: Exit code produced by filter and child actions.
        """
        # If the author doesn't match, don't do anything.
        if not self.regex.search(self.author): return 0

        # Execute the child actions.
        self.context.tokens['Author'] = self.author
        return super(FilterAuthor, self).run()

class FilterBreakUnlock(Filter):
    """Break Unlock Flag Filter Class

    Determine if removing another user's path lock.

    Input Tokens: BreakUnlock
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterBreakUnlock, self).__init__(*args, **kwargs)

        # Get the comparison sense flag.
        self.sense = self.get_boolean('sense', default=True)
        logger.debug('sense = {0}'.format(self.sense))

        # Get the filter parameters.
        self.breakunlock = (
            self.context.tokens['BreakUnlock'] == '1')
        logger.debug('breakunlock = {0}'.format(self.breakunlock))

    def run(self):
        """If the flag matches the filter sense, run child actions.

        Returns: Exit code from filter or child actions.
        """
        # Check for a condition mismatch.
        if (self.sense and (not self.breakunlock)) \
                or ((not self.sense) and self.breakunlock):
            return 0

        # Execute the child actions.
        return super(FilterBreakUnlock, self).run()

class FilterCapabilities(Filter):
    """Client Capabilities Filter Class

    Look for a match with the client capabilities.

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

        # Get the capabilities string.
        self.capabilities = self.context.tokens['Capabilities']
        logger.debug('capabilities = "{0}"'.format(self.capabilities))

    def run(self):
        """If client capabilities match, run actions.

        Returns: Exit code produced by filter and child actions.
        """
        # If the capabilities don't match, do nothing.
        if not self.regex.search(self.capabilities): return 0

        # Perform the child actions.
        return super(FilterCapabilities, self).run()

class FilterChgType(Filter):
    """RevProp Change Type Filter Class

    Look for a revision property change type.

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

        # Get the change type string.
        self.chgtype = self.context.tokens['ChgType']
        logger.debug('chgtype = "{0}"'.format(self.chgtype))

    def run(self):
        """If revprop change types match, run actions.

        Returns: Exit code produced by filter and child actions.
        """
        # If the change type doesn't match, do nothing.
        if not self.regex.match(self.chgtype): return 0

        # Perform the child actions.
        return super(FilterChgType, self).run()

class FilterComment(Filter):
    """Lock Comment Filter Class

    Look for a lock comment.

    Input Tokens: Comment
    Input Tags: CommentRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterComment, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('CommentRegex')
        if regextag == None:
            raise ValueError('Required tag missing: CommentRegex')
        self.regex = RegexTag(regextag)

        # Get the lock comment.
        self.comment = self.context.tokens['Comment']
        logger.debug('comment = "{0}"'.format(self.comment))

    def run(self):
        """If lock comment matches, run actions.

        Returns: Exit code produced by filter and child actions.
        """
        # If the comment doesn't match, do nothing.
        if not self.regex.search(self.comment): return 0

        # Perform the child actions.
        return super(FilterComment, self).run()

class FilterCommitList(Filter):
    """Commit List Filter Class

    Look for a match in the list of commit list paths.

    Input Tokens: ReposPath, Transaction, Revision
    Input Tags: PathRegex, ChgTypeRegex
    Output Tokens: Path, ChgType
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterCommitList, self).__init__(*args, **kwargs)

        # Save the "stop on first match" flag.
        self.matchfirst = self.get_boolean('matchFirst')
        logger.debug('matchFirst = {0}'.format(self.matchfirst))

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
        if self.typeregex == None and self.pathregex == None:
            raise ValueError(
                'Required tag missing: PathRegex or ChgTypeRegex')

    def run(self):
        """Filter actions based on changes.

        Returns: Exit code produced by filter and child actions.
        """
        # Get the dictionary of changes.
        changes = self.context.get_changes()

        # Compare the changes to the regular expressions.
        for change in changes:
            logger.debug('path = "{0}"'.format(change.path))
            logger.debug('chgtype = "{0}"'.format(change.type))

            # Check for a change path mismatch.
            if self.pathregex \
                    and not self.pathregex.search(change.path):
                continue

            # Check for a change type mismatch.
            if self.typeregex \
                    and not self.typeregex.match(change.type):
                continue

            # Save the triggering change details.
            self.context.tokens['Path'] = change.path
            self.context.tokens['ChgType'] = change.type

            # Execute the child actions. If they produce a non-zero
            # exit code, or if only looking for the first match, stop
            # checking.
            exitcode = super(FilterCommitList, self).run()
            if exitcode or self.matchfirst: return exitcode

        # Either nothing matched, or the child actions were
        # successful.
        return 0

class FilterFileContent(Filter):
    """File Content Filter Class

    Check for content in an included file.

    Input Tokens: ReposPath, Transaction, Revision, Path
    """

    def __init__(self, *args, **kwargs):
        """Get the filter execution parameters."""

        # Construct the base instance.
        super(FilterFileContent, self).__init__(*args, **kwargs)

        # Get the regular expression tag evaluator.
        regextag = self.thistag.find('ContentRegex')
        if regextag == None:
            raise ValueError('Required tag missing: ContentRegex')
        self.regex = RegexTag(regextag)

        # Get the current path. (This may point to a folder.)
        self.path = self.context.tokens['Path']
        logger.debug('path = "{0}"'.format(self.path))
        
    def run(self):
        """Filter actions based on file content.

        Returns: Exit code produced by filter and child actions.
        """
        # Silently ignore folder paths.
        if re.search(r'/$', self.path): return 0

        # Get the indicated file content.
        content = self.context.get_file_content(self.path)

        # If the content doesn't match, do nothing.
        if not self.regex.search(content): return 0

        # Perform the child actions.
        return super(FilterFileContent, self).run()

class FilterLockOwner(Filter):
    """Lock Owner Filter Class

    Determine if the user is or is not the lock owner.

    Input Tokens: ReposPath, Path, User
    Output Tokens: Owner
    """

    def __init__(self, *args, **kwargs):
        """Get the filter execution parameters."""

        # Construct the base instance.
        super(FilterLockOwner, self).__init__(*args, **kwargs)

        # Get the filter sense flag.
        self.sense = self.get_boolean('sense', default=True)
        logger.debug('sense = {0}'.format(self.sense))

        # Get the lock location.
        self.repospath = self.context.tokens['ReposPath']
        self.path = self.context.tokens['Path']

        # Get the current user.
        self.user = self.context.tokens['User']

        # Request the path lock details. Since this is a low-volume
        # hook, there's no need to cache the result.
        cmd = ['svnlook', 'lock', self.repospath, self.path]
        logger.debug('Execute: {0}'.format(cmd))
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)

        # If unable to execute, complain.
        except Exception as e:
            logger.error(e)
            raise e

        # The process started, wait for it to finish.
        p.wait()

        # Handle a command failure.
        if p.returncode != 0:
            errstr = p.stderr.read().strip()
            msg = 'Command failed: {0}: {1}'.format(cmd, errstr)
            logger.error(msg)
            raise RuntimeError(msg)

        # Extract the lock owner name.
        self.owner = None
        for line in p.stdout.readlines():
            logger.debug('line = "{0}"'.format(line.rstrip()))
            
            # Skip the other lines.
            owner = re.match(r'Owner:\s+(\S+)', line.rstrip())
            if not owner: continue

            # Save the lock owner and stop looking.
            self.owner = owner.group(1)
            logger.debug('owner = "{0}"'.format(self.owner))
            return

        # Log that it's a new lock.
        logger.debug('owner = None')

    def run(self):
        """Filter actions based on lock ownership.

        Returns: Exit code produced by filter and child actions.
        """
        # Determine if this filter doesn't apply.
        if (self.owner == None \
                or (self.sense and self.user != self.owner) \
                or ((not self.sense) and self.user == self.owner)):
            return 0

        # Perform the child actions.
        self.context.tokens['Owner'] = self.owner
        return super(FilterLockOwner, self).run()

class FilterLockToken(Filter):
    """Lock Token Filter Class

    Check the lock token name.

    Input Tokens: LockToken
    Input Tags: LockTokenRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterLockToken, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator for the names.
        regextag = self.thistag.find('LockTokenRegex')
        if regextag == None:
            raise ValueError('Required tag missing: LockTokenRegex')
        self.regex = RegexTag(regextag)

        # Get the actual lock token.
        self.locktoken = self.context.tokens['LockToken']
        logger.debug('locktoken = "{0}"'.format(self.locktoken))

    def run(self):
        """Filter actions based on lock tokens.

        Returns: Exit code produced by filter and child actions.
        """
        # Handle a mismatch with the lock token.
        if not self.regex.match(self.locktoken): return 0

        # Execute the child actions.
        return super(FilterLockToken, self).run()

class FilterLogMsg(Filter):
    """Log Message Filter Class

    Check the commit message.

    Input Tokens: ReposPath, Transaction or Revision
    Input Tags: LogMsgRegex
    Output Tokens: LogMsg
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterLogMsg, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('LogMsgRegex')
        if regextag == None:
            raise ValueError('Required tag missing: LogMsgRegex')
        self.regex = RegexTag(regextag)

        # Get the current log message.
        self.logmsg = self.context.get_log_message()
        logger.debug('logmsg = "{0}"'.format(self.logmsg))

    def run(self):
        """Filter actions based on log message.

        Returns: Exit code produced by filter and child actions.
        """
        # If the log message doesn't match, don't do anything.
        if not self.regex.search(self.logmsg): return 0

        # Execute the child actions.
        self.context.tokens['LogMsg'] = self.logmsg
        return super(FilterLogMsg, self).run()

class FilterPath(Filter):
    """Single Path Filter Class

    Check for a match with a single path name.

    Input Tokens: Path
    Input Tags: PathRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterPath, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('PathRegex')
        if regextag == None:
            raise ValueError('Required tag missing: PathRegex')
        self.regex = RegexTag(regextag)

        # Get the path name.
        self.path = self.context.tokens['Path']
        logger.debug('path = "{0}"'.format(self.path))

    def run(self):
        """Filter operations based on current path name.

        Returns: Exit code produced by filter and child actions.
        """
        # If the path name doesn't match, do nothing.
        if not self.regex.search(self.path): return

        # Execute the child actions.
        return super(FilterPath, self).run()

class FilterPathList(Filter):
    """Path List Filter Class

    Check for a path in a list of paths.

    Input Tokens: Paths
    Input Tags: PathRegex
    Output Tokens: Path
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterPathList, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('PathRegex')
        if regextag == None:
            raise ValueError('Required tag missing: PathRegex')
        self.regex = RegexTag(regextag)

        # Get the "look for the first match" flag.
        self.matchfirst = self.get_boolean('matchFirst')
        logger.debug('matchfirst = {0}'.format(self.matchfirst))

        # Get the list of path names.
        self.paths = self.context.tokens['Paths']
        logger.debug('paths = {0}'.format(self.paths))

    def run(self):
        """Filter operations based on current path name.

        Returns: Exit code produced by filter and child actions.
        """
        # Look through the path names.
        for path in self.paths:

            # If the path name doesn't match, do nothing.
            if not self.regex.search(path): return

            # Execute the child actions.
            self.context.tokens['Path'] = path
            exitcode = super(FilterPathList, self).run()

            # If only looking for the first, or an error is reported,
            # bail out early.
            if self.matchfirst or exitcode != 0: return exitcode

        # None of the path names matched.
        return 0

class FilterPropList(Filter):
    """Property List Filter Class

    Check for a property in the list for a path.

    Input Tags: PropNameRegex, PropValueRegex
    Input Tokens: ReposPath, Path
    Output Tokens: PropName, PropValue
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterPropList, self).__init__(*args, **kwargs)

        # Construct the regular expression tag evaluators.
        nameregextag = self.thistag.find('PropNameRegex')
        if nameregextag != None:
            self.nameregex = RegexTag(nameregextag)
        else:
            self.nameregex = None

        valueregextag = self.thistag.find('PropValueRegex')
        if valueregextag != None:
            self.valueregex = RegexTag(valueregextag)
        else:
            self.valueregex = None

        # Make sure that at least one regular expression is specified.
        if self.nameregex == None and self.valueregex == None:
            raise ValueError('Required tag missing: '\
                                 'PropNameRegex or PropValueRegex')

        # Get the "look for the first match" flag.
        self.matchfirst = self.get_boolean('matchFirst')
        logger.debug('matchfirst = {0}'.format(self.matchfirst))

        # Get the path name.
        self.path = self.context.tokens['Path']
        logger.debug('path = {0}'.format(self.path))

    def run(self):
        """Filter operations based on current path properties.

        Returns: Exit code produced by filter and child actions.
        """
        # Look through the properties.
        for name, value in \
                self.context.get_properties(self.path).items():

            # If the name doesn't match, skip this one.
            if self.nameregex \
                    and not self.nameregex.match(name): continue

            # If the value doesn't match, skip this one.
            if self.valueregex \
                    and not self.valueregex.search(value): continue

            # Execute the child actions.
            self.context.tokens['PropName'] = name
            self.context.tokens['PropValue'] = value
            exitcode = super(FilterPropList, self).run()

            # If only looking for the first, or an error is reported,
            # bail out early.
            if self.matchfirst or exitcode != 0: return exitcode

        # Handle a non-error exit.
        return 0

class FilterRevProp(Filter):
    """Revision Property Filter Class

    Check for a revision property match.

    Input Tokens: RevPropName, RevPropValue
    Input Tags: PropNameRegex, PropValueRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterRevProp, self).__init__(*args, **kwargs)

        # Construct regular expression tag evaluators.
        nameregextag = self.thistag.find('PropNameRegex')
        if nameregextag != None:
            self.nameregex = RegexTag(nameregextag)
        else:
            self.nameregex = None

        valueregextag = self.thistag.find('PropValueRegex')
        if valueregextag != None:
            self.valueregex = RegexTag(valueregextag)
        else:
            self.valueregex = None

        # Make sure that at least one regular expression is specified.
        if self.nameregex == None and self.valueregex == None:
            raise ValueError('Required tag missing: '\
                                 'PropNameRegex or PropValueRegex')

        # Save the revision property details.
        self.propname = self.context.tokens['RevPropName']
        logger.debug('propname = {0}'.format(self.propname))
        self.propvalue = self.context.tokens['RevPropValue']
        logger.debug('propvalue = "{0}"'.format(self.propvalue))

    def run(self):
        """Filter operations based on revision property.

        Returns: Exit code produced by filter and child actions.
        """
        # If the name doesn't match, do nothing.
        if self.nameregex and \
                not self.nameregex.match(self.propname): return 0

        # If the value doesn't match, do nothing.
        if self.valueregex and \
                not self.valueregex.search(self.propvalue): return 0

        # Execute the child actions.
        return super(FilterRevProp, self).run()

class FilterStealLock(Filter):
    """Steal Lock Flag Filter Class

    Determine if taking over another user's path lock.

    Input Tokens: StealLock
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterStealLock, self).__init__(*args, **kwargs)

        # Get the comparison sense flag.
        self.sense = self.get_boolean('sense', default=True)
        logger.debug('sense = {0}'.format(self.sense))

        # Get the filter parameters.
        self.steallock = (
            self.context.tokens['StealLock'] == '1')
        logger.debug('steallock = {0}'.format(self.steallock))

    def run(self):
        """If the flag matches the filter sense, run child actions.

        Returns: Exit code from filter or child actions.
        """
        # Check for a condition mismatch.
        if (self.sense and (not self.steallock)) \
                or ((not self.sense) and self.steallock):
            return 0

        # Execute the child actions.
        return super(FilterStealLock, self).run()

class FilterUser(Filter):
    """User Name Filter Class

    Checks for a matching user name.

    Input Tokens: User
    Input Tags: UserRegex
    """

    def __init__(self, *args, **kwargs):
        """Read parameters from filter configuration."""

        # Construct the base instance.
        super(FilterUser, self).__init__(*args, **kwargs)

        # Construct a regular expression tag evaluator.
        regextag = self.thistag.find('UserRegex')
        if regextag == None:
            raise ValueError('Required tag missing: UserRegex')
        self.regex = RegexTag(regextag, re.IGNORECASE)

        # Get the user name.
        self.user = self.context.tokens['User']
        logger.debug('user = "{0}"'.format(self.user))

    def run(self):
        """Filter operations based on user name.

        Returns: Exit code produced by filter and child actions.
        """
        # If the user name doesn't match, do nothing.
        if not self.regex.match(self.user): return 0

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
                'Required tag content missing: {0}'\
                    .format(regextag.tag))

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
