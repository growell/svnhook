#!/bin/bash

# START-COMMIT HOOK
#
# The start-commit hook is invoked before a Subversion txn is created
# in the process of doing a commit.  Subversion runs this hook
# by invoking a program (script, executable, binary, etc.) named
# 'start-commit' (for which this file is a template)
# with the following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] USER         (the authenticated user attempting to commit)
#   [3] CAPABILITIES (a colon-separated list of capabilities reported
#                     by the client; see note below)
#
# Note: The CAPABILITIES parameter is new in Subversion 1.5, and 1.5
# clients will typically report at least the "mergeinfo" capability.
# If there are other capabilities, then the list is colon-separated,
# e.g.: "mergeinfo:some-other-capability" (the order is undefined).
#
# The list is self-reported by the client.  Therefore, you should not
# make security assumptions based on the capabilities list, nor should
# you assume that clients reliably report every capability they have.
#
# The working directory for this hook program's invocation is undefined,
# so the program should set one explicitly if it cares.
#
# If the hook program exits with success, the commit continues; but
# if it exits with failure (non-zero), the commit is stopped before
# a Subversion txn is created, and STDERR is returned to the client.
#
# On a Unix system, the normal procedure is to have 'start-commit'
# invoke other programs to do the real work, though it may do the
# work itself too.
#
# Note that 'start-commit' must be executable by the user(s) who will
# invoke it (typically the user httpd runs as), and that user must
# have filesystem-level permission to access the repository.
#
# On a Windows system, you should name the hook program
# 'start-commit.bat' or 'start-commit.exe',
# but the basic idea is the same.
# 
# The hook program typically does not inherit the environment of
# its parent process.  For example, a common problem is for the
# PATH environment variable to not be set to its usual value, so
# that subprograms fail to launch unless invoked via absolute path.
# If you're having unexpected problems with a hook program, the
# culprit may be unusual (or missing) environment variables.

cd "$1"
HOOK=../../../../bin/svnhook-start-commit
python $HOOK "$1" "$2" "$3" --cfgfile=conf/start-commit.xml

########################### end of file ##############################
