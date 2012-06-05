#!/bin/bash

# PRE-UNLOCK HOOK
#
# The pre-unlock hook is invoked before an exclusive lock is
# destroyed.  Subversion runs this hook by invoking a program 
# (script, executable, binary, etc.) named 'pre-unlock' (for which
# this file is a template), with the following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] PATH         (the path in the repository about to be unlocked)
#   [3] USER         (the user destroying the lock)
#   [4] TOKEN        (the lock token to be destroyed)
#   [5] BREAK-UNLOCK (1 if the user is breaking the lock, else 0)
#
# The default working directory for the invocation is undefined, so
# the program should set one explicitly if it cares.
#
# If the hook program exits with success, the lock is destroyed; but
# if it exits with failure (non-zero), the unlock action is aborted
# and STDERR is returned to the client.

# On a Unix system, the normal procedure is to have 'pre-unlock'
# invoke other programs to do the real work, though it may do the
# work itself too.
#
# Note that 'pre-unlock' must be executable by the user(s) who will
# invoke it (typically the user httpd runs as), and that user must
# have filesystem-level permission to access the repository.
#
# On a Windows system, you should name the hook program
# 'pre-unlock.bat' or 'pre-unlock.exe',
# but the basic idea is the same.

cd "$1"
HOOK=../../../../bin/svnhook-pre-unlock
python $HOOK "$1" "$2" "$3" "$4" $5 --cfgfile=conf/pre-unlock.xml

########################### end of file ##############################
