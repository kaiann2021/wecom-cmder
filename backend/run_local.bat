@echo off
REM Set PYTHONPATH to include user site-packages where pycryptodome is installed
set PYTHONPATH=%PYTHONPATH%;C:\Users\hewj\AppData\Roaming\Python\Python311\site-packages

if not exist data mkdir data

echo Starting server...
python -m app.main
pause
