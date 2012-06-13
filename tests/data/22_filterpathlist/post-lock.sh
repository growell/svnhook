#!/bin/bash

# POST-LOCK HOOK
#
# The post-lock hook is run after a path is locked.  Subversion runs
# this hook by invoking a program (script, executable, binary, etc.)
# named 'post-lock' (for which this file is a template) with the 
# following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] USER         (the user who created the lock)
#
# The paths that were just locked are passed to the hook via STDIN (as
# of Subversion 1.2, only one path is passed per invocation, but the
# plan is to pass all locked paths at once, so the hook program
# should be written accordingly).
#
# The default working directory for the invocation is undefined, so
# the program should set one explicitly if it cares.
#
# Because the lock has already been created and cannot be undone,
# the exit code of the hook program is ignored.  The hook program
# can use the 'svnlook' utility to help it examine the
# newly-created lock.
#
# On a Unix system, the normal procedure is to have 'post-lock'
# invoke other programs to do the real work, though it may do the
# work itself too.
#
# Note that 'post-lock' must be executable by the user(s) who will
# invoke it (typically the user httpd runs as), and that user must
# have filesystem-level permission to access the repository.
#
# On a Windows system, you should name the hook program
# 'post-lock.bat' or 'post-lock.exe',
# but the basic idea is the same.

cd "$1"
HOOK=../../../../bin/svnhook-post-lock
python $HOOK "$1" $2 --cfgfile=conf/post-lock.xml

########################### end of file ##############################
