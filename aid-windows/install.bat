CLS
ECHO OFF

REM Batch script to install aid on windows

SETLOCAL ENABLEDELAYEDEXPANSION

@echo Administrative permissions required. Detecting permissions...

net session >nul 2>&1
if %errorLevel% == 0 (
   @echo Success: Administrative permissions confirmed.
) else (
   @echo Failure: Current permissions inadequate.
   exit /B
)

for /F "tokens=1,2,3,4,5" %%A in ('"dir C:\ | find "Python""') DO (
   set _pyversion=%%E
)

if [%_pyversion%] == [] (
   @echo Error: Python not found in root directory of C:\
   @echo Please install python 2.7 to this location^^! 
   exit /B
)

set _result=%_pyversion:~6,7%

if %_result%==27 (
   @echo Python is version 2.7 - good to continue^^!
) else (
   @echo ERROR: Python version is not 2.7^^! 
   @echo Please install python 2.7 to continue^^!
   exit /B
)

@echo Creating directories and copying files...
mkdir "C:\Program Files\AID"
mkdir "C:\Program Files\AID\etc"
mkdir "C:\Program Files\AID\plugins"
mkdir "C:\Program Files\AID\logs"
xcopy "install-files\aid-agent.pyw" "C:\Program Files\AID\"
xcopy "install-files\start.bat" "C:\Program Files\AID\"
xcopy "install-files\etc\aid.conf" "C:\Program Files\AID\etc"
xcopy "install-files\etc\logging.conf" "C:\Program Files\AID\etc"
xcopy /s "install-files\plugins" "C:\Program Files\AID\plugins"

@echo Creating firewall rule
netsh advfirewall firewall add rule name="AID incoming port allow" dir=in action=allow protocol=TCP localport=8080 remoteip=

@echo Setting up AID to start on reboot
SchTasks /Create /tn "AID startup" /sc "ONSTART" /tr "C:\Python27\pythonw.exe \"C:\Program Files\AID\aid-agent.pyw\"" /ru "SYSTEM"

@echo Complete^^!
@echo For this time only, go into Scheduled tasks and Right click the new task and click Run. Normally it will start on Reboot

@pause
