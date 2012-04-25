@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM PRE-COMMIT HOOK
REM
REM The pre-commit hook is invoked before a Subversion txn is
REM committed.  Subversion runs this hook by invoking a program
REM (script, executable, binary, etc.) named 'pre-commit' (for which
REM this file is a template), with the following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] TXN-NAME     (the name of the txn about to be committed)
REM
REM   [STDIN] LOCK-TOKENS ** the lock tokens are passed via STDIN.
REM
REM   If STDIN contains the line "LOCK-TOKENS:\n" (the "\n" denotes a
REM   single newline), the lines following it are the lock tokens for
REM   this commit.  The end of the list is marked by a line containing
REM   only a newline character.
REM
REM   Each lock token line consists of a URI-escaped path, followed
REM   by the separator character '|', followed by the lock token string,
REM   followed by a newline.
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM If the hook program exits with success, the txn is committed; but
REM if it exits with failure (non-zero), the txn is aborted, no commit
REM takes place, and STDERR is returned to the client.   The hook
REM program can use the 'svnlook' utility to help it examine the txn.
REM
REM On a Unix system, the normal procedure is to have 'pre-commit'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM   ***  NOTE: THE HOOK PROGRAM MUST NOT MODIFY THE TXN, EXCEPT  ***
REM   ***  FOR REVISION PROPERTIES (like svn:log or svn:author).   ***
REM
REM   This is why we recommend using the read-only 'svnlook' utility.
REM   In the future, Subversion may enforce the rule that pre-commit
REM   hooks should not modify the versioned data in txns, or else come
REM   up with a mechanism to make it safe to do so (by informing the
REM   committing client of the changes).  However, right now neither
REM   mechanism is implemented, so hook writers just have to be careful.
REM
REM Note that 'pre-commit' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'pre-commit.bat' or 'pre-commit.exe',
REM but the basic idea is the same.
REM
REM The hook program typically does not inherit the environment of
REM its parent process.  For example, a common problem is for the
REM PATH environment variable to not be set to its usual value, so
REM that subprograms fail to launch unless invoked via absolute path.
REM If you're having unexpected problems with a hook program, the
REM culprit may be unusual (or missing) environment variables.

cd /d %~dp0
python ..\..\..\bin\pre-commit "%1" "%2" --cfgfile=conf\pre-commit.xml

REM ####################### end of file ##############################
