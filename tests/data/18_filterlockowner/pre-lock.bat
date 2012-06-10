@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM PRE-LOCK HOOK
REM
REM The pre-lock hook is invoked before an exclusive lock is
REM created.  Subversion runs this hook by invoking a program 
REM (script, executable, binary, etc.) named 'pre-lock' (for which
REM this file is a template), with the following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] PATH         (the path in the repository about to be locked)
REM   [3] USER         (the user creating the lock)
REM   [4] COMMENT      (the comment of the lock)
REM   [5] STEAL-LOCK   (1 if the user is trying to steal the lock, else 0)
REM
REM If the hook program outputs anything on stdout, the output string will
REM be used as the lock token for this lock operation.  If you choose to use
REM this feature, you must guarantee the tokens generated are unique across
REM the repository each time.
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM If the hook program exits with success, the lock is created; but
REM if it exits with failure (non-zero), the lock action is aborted
REM and STDERR is returned to the client.

REM On a Unix system, the normal procedure is to have 'pre-lock'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'pre-lock' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'pre-lock.bat' or 'pre-lock.exe',
REM but the basic idea is the same.

cd /d %1
set HOOK=..\..\..\..\bin\svnhook-pre-lock
python "%HOOK%" %1 %2 %3 %4 %5 --cfgfile=conf\pre-lock.xml
exit %errorlevel%

REM ####################### end of file #############################
