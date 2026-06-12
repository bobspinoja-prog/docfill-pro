@echo off
setlocal

set "APPDIR=%LOCALAPPDATA%\DocFillPro"
set "APP_EXE=%APPDIR%\DOCFILL PRO.exe"

if not exist "%APPDIR%" mkdir "%APPDIR%"
copy /Y "%~dp0DOCFILL_PRO.exe" "%APP_EXE%" >nul
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$shell = New-Object -ComObject WScript.Shell; $target = Join-Path $env:LOCALAPPDATA 'DocFillPro\DOCFILL PRO.exe'; $workdir = Split-Path $target; $desktop = [Environment]::GetFolderPath('Desktop'); $shortcut = $shell.CreateShortcut((Join-Path $desktop 'DOCFILL PRO.lnk')); $shortcut.TargetPath = $target; $shortcut.WorkingDirectory = $workdir; $shortcut.Save(); $programs = [Environment]::GetFolderPath('Programs'); $shortcut = $shell.CreateShortcut((Join-Path $programs 'DOCFILL PRO.lnk')); $shortcut.TargetPath = $target; $shortcut.WorkingDirectory = $workdir; $shortcut.Save()"

start "" "%APP_EXE%"
endlocal
exit /b 0
