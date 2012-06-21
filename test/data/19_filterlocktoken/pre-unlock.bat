@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM PRE-UNLOCK HOOK
REM
REM The pre-unlock hook is invoked before an exclusive lock is
REM destroyed.  Subversion runs this hook by invoking a program 
REM (script, executable, binary, etc.) named 'pre-unlock' (for which
REM this file is a template), with the following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] PATH         (the path in the repository about to be unlocked)
REM   [3] USER         (the user destroying the lock)
REM   [4] TOKEN        (the lock token to be destroyed)
REM   [5] BREAK-UNLOCK (1 if the user is breaking the lock, else 0)
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM If the hook program exits with success, the lock is destroyed; but
REM if it exits with failure (non-zero), the unlock action is aborted
REM and STDERR is returned to the client.

REM On a Unix system, the normal procedure is to have 'pre-unlock'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'pre-unlock' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'pre-unlock.bat' or 'pre-unlock.exe',
REM but the basic idea is the same.

cd /d %1
set HOOK=..\..\..\..\bin\svnhook-pre-unlock
python "%HOOK%" %1 %2 %3 %4 %5 --cfgfile=conf\pre-unlock.xml
exit %errorlevel%

REM ####################### end of file #############################
