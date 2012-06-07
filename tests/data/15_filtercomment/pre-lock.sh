#!/bin/bash

# PRE-LOCK HOOK
#
# The pre-lock hook is invoked before an exclusive lock is
# created.  Subversion runs this hook by invoking a program 
# (script, executable, binary, etc.) named 'pre-lock' (for which
# this file is a template), with the following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] PATH         (the path in the repository about to be locked)
#   [3] USER         (the user creating the lock)
#   [4] COMMENT      (the comment of the lock)
#   [5] STEAL-LOCK   (1 if the user is trying to steal the lock, else 0)
#
# If the hook program outputs anything on stdout, the output string will
# be used as the lock token for this lock operation.  If you choose to use
# this feature, you must guarantee the tokens generated are unique across
# the repository each time.
#
# The default working directory for the invocation is undefined, so
# the program should set one explicitly if it cares.
#
# If the hook program exits with success, the lock is created; but
# if it exits with failure (non-zero), the lock action is aborted
# and STDERR is returned to the client.

# On a Unix system, the normal procedure is to have 'pre-lock'
# invoke other programs to do the real work, though it may do the
# work itself too.
#
# Note that 'pre-lock' must be executable by the user(s) who will
# invoke it (typically the user httpd runs as), and that user must
# have filesystem-level permission to access the repository.
#
# On a Windows system, you should name the hook program
# 'pre-lock.bat' or 'pre-lock.exe',
# but the basic idea is the same.

cd "$1"
HOOK=../../../../bin/svnhook-pre-lock
python $HOOK "$1" "$2" "$3" "$4" $5 --cfgfile=conf/pre-lock.xml

########################### end of file ##############################
