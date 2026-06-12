@echo off
setlocal
cd /d "%~dp0"
set PORT=8080
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4"') do (
  set IP=%%A
  goto :gotip
)
:gotip
set IP=%IP: =%
echo.
echo Dashboard de produtividade dispon?vel na rede local:
echo.
echo   http://%IP%:%PORT%/dashboard_produtividade_completo.html
echo.
echo Mantenha esta janela aberta enquanto quiser acessar pelo celular, tablet ou notebook.
echo Para parar, pressione CTRL+C e confirme.
echo.
py -m http.server %PORT% --bind 0.0.0.0
if errorlevel 1 python -m http.server %PORT% --bind 0.0.0.0
pause