@echo off
setlocal

set VENV_NAME=.venv

if not exist %VENV_NAME% (
    echo Virtual environment '%VENV_NAME%' not found. Creating the virtual environment...
    C:\Users\swill\AppData\Local\Programs\Python\Python37\python.exe -m venv %VENV_NAME%
)

call %VENV_NAME%\Scripts\activate

pip install -r requirements.txt

deactivate

echo Installation completed.
exit /b 0
