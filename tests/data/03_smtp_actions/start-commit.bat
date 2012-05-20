@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM START-COMMIT HOOK
REM
REM The start-commit hook is invoked before a Subversion txn is created
REM in the process of doing a commit.  Subversion runs this hook
REM by invoking a program (script, executable, binary, etc.) named
REM 'start-commit' (for which this file is a template)
REM with the following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] USER         (the authenticated user attempting to commit)
REM   [3] CAPABILITIES (a colon-separated list of capabilities reported
REM                     by the client; see note below)
REM
REM Note: The CAPABILITIES parameter is new in Subversion 1.5, and 1.5
REM clients will typically report at least the "mergeinfo" capability.
REM If there are other capabilities, then the list is colon-separated,
REM e.g.: "mergeinfo:some-other-capability" (the order is undefined).
REM
REM The list is self-reported by the client.  Therefore, you should not
REM make security assumptions based on the capabilities list, nor should
REM you assume that clients reliably report every capability they have.
REM
REM The working directory for this hook program's invocation is undefined,
REM so the program should set one explicitly if it cares.
REM
REM If the hook program exits with success, the commit continues; but
REM if it exits with failure (non-zero), the commit is stopped before
REM a Subversion txn is created, and STDERR is returned to the client.
REM
REM On a Unix system, the normal procedure is to have 'start-commit'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'start-commit' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'start-commit.bat' or 'start-commit.exe',
REM but the basic idea is the same.
REM 
REM The hook program typically does not inherit the environment of
REM its parent process.  For example, a common problem is for the
REM PATH environment variable to not be set to its usual value, so
REM that subprograms fail to launch unless invoked via absolute path.
REM If you're having unexpected problems with a hook program, the
REM culprit may be unusual (or missing) environment variables.

cd /d %1
set HOOK=%SVNHOOK_HOME~%\bin\svnhook-start-commit
python "%HOOK%" %1 %2 %3 --cfgfile=conf\start-commit.xml
exit %errorlevel%

REM ####################### end of file #############################
