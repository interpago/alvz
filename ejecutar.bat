@echo off
if "%1"=="" (
    echo Error: Debes proporcionar un archivo .alvz
    echo Ejemplo: .\ejecutar tutorial_bucles.alvz
    exit /b
)
python "%~dp0alvz.py" %1
