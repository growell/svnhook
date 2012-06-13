@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM POST-LOCK HOOK
REM
REM The post-lock hook is run after a path is locked.  Subversion runs
REM this hook by invoking a program (script, executable, binary, etc.)
REM named 'post-lock' (for which this file is a template) with the 
REM following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] USER         (the user who created the lock)
REM
REM The paths that were just locked are passed to the hook via STDIN (as
REM of Subversion 1.2, only one path is passed per invocation, but the
REM plan is to pass all locked paths at once, so the hook program
REM should be written accordingly).
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM Because the lock has already been created and cannot be undone,
REM the exit code of the hook program is ignored.  The hook program
REM can use the 'svnlook' utility to help it examine the
REM newly-created lock.
REM
REM On a Unix system, the normal procedure is to have 'post-lock'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'post-lock' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'post-lock.bat' or 'post-lock.exe',
REM but the basic idea is the same.

cd /d %1
set HOOK=..\..\..\..\bin\svnhook-post-lock
python "%HOOK%" %1 %2 --cfgfile=conf\post-lock.xml
exit %errorlevel%

REM ####################### end of file #############################
