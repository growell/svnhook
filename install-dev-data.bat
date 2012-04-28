@ECHO OFF
REM ##################################################################
REM Install Development Data for Windows
REM ##################################################################
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM Get this script location as the SvnHook directory.
SET SVNHOOK_DIR=%~dp0

REM Set up the test repositories.
CALL :MKREPO 1
GOTO :EOF

:MKREPO
REM Define the indexed repository setup function.

SET REPO_NUM=%1
SET REPO_DIR=repo_%REPO_NUM%
SET REPO_SRC=data\%REPO_NUM%\windows

REM Change into the test directory.
SET ROOT_DIR=%SVNHOOK_DIR%SvnHook\test
PUSHD %ROOT_DIR%

REM Construct the repository URL.
SET REPO_URL=file:///%ROOT_DIR:\=/%/%REPO_DIR%
ECHO REPO_URL='%REPO_URL%'

REM If the test repository exists, remove it.
IF EXIST %REPO_DIR% (
  ECHO Removing old '%REPO_DIR%' repository...
  RMDIR /S /Q %REPO_DIR%
)

REM Create the test repository.
ECHO Creating new '%REPO_DIR%' repository...
svnadmin create %REPO_DIR%

REM Create the hook log directory.
MKDIR %REPO_DIR%\logs

REM Copy the hook configuration files into the repository.
FOR %%a IN (%REPO_SRC%\*.xml) DO (
  ECHO Copying %%~nxa to %REPO_DIR%\conf ...
  COPY %%a %REPO_DIR%\conf >NUL:
)
FOR %%a IN (%REPO_SRC%\*-log.yml) DO (
  ECHO Copying %%~nxa to %REPO_DIR%\conf ...
  COPY %%a %REPO_DIR%\conf >NUL:
)
FOR %%a IN (%REPO_SRC%\*-log.conf) DO (
  ECHO Copying %%~nxa to %REPO_DIR%\conf ...
  COPY %%a %REPO_DIR%\conf >NUL:
)

REM Copy the hook scripts into the repository.
FOR %%a IN (%REPO_SRC%\*.bat) DO (
  ECHO Copying %%~nxa to %REPO_DIR%\hooks ...
  COPY %%a %REPO_DIR%\hooks >NUL:
)

REM Execute any initial Subversion commands.
IF EXIST %REPO_SRC%\setup_svn.bat (
  CALL %REPO_SRC%\setup_svn.bat %REPO_URL%
)

EXIT /B 0

REM ####################### end of file ##############################
