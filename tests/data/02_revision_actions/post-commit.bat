@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM POST-COMMIT HOOK
REM
REM The post-commit hook is invoked after a commit.  Subversion runs
REM this hook by invoking a program (script, executable, binary, etc.)
REM named 'post-commit' (for which this file is a template) with the 
REM following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] REV          (the number of the revision just committed)
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM Because the commit has already completed and cannot be undone,
REM the exit code of the hook program is ignored.  The hook program
REM can use the 'svnlook' utility to help it examine the
REM newly-committed tree.
REM
REM On a Unix system, the normal procedure is to have 'post-commit'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'post-commit' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'post-commit.bat' or 'post-commit.exe',
REM but the basic idea is the same.
REM 
REM The hook program typically does not inherit the environment of
REM its parent process.  For example, a common problem is for the
REM PATH environment variable to not be set to its usual value, so
REM that subprograms fail to launch unless invoked via absolute path.
REM If you're having unexpected problems with a hook program, the
REM culprit may be unusual (or missing) environment variables.

cd /d %1
python ..\..\..\bin\post-commit %1 %2 --cfgfile=conf\post-commit.xml
exit %errorlevel%

REM ####################### end of file #############################
