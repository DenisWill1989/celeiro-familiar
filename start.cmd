@echo off
TITLE Celeiro Familiar - Servidor Local Familiar
color 0A
echo ========================================================
echo        CELEIRO FAMILIAR - CONTROLE FINANCEIRO FAMILIAR
echo ========================================================
echo.
echo [1/3] Verificando dependencias Python...
python -m pip install -r requirements.txt --quiet

echo.
echo [2/3] Descobrindo IP local na rede Wi-Fi...
for /f "tokens=2 delims=[]" %%a in ('ping -n 1 %computername%') do set LOCAL_IP=%%a

echo.
echo [3/3] Iniciando o servidor local...
echo.
echo --------------------------------------------------------
echo  ACESSO NO SEU NOTEBOOK (este computador):
echo  http://localhost:8000
echo.
echo  ACESSO NO NOTEBOOK DA SUA ESPOSA (na mesma rede Wi-Fi):
echo  http://%COMPUTERNAME%:8000
echo  (ou use o IP local da maquina principal)
echo --------------------------------------------------------
echo.
echo Pressione CTRL+C para encerrar o servidor a qualquer momento.
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
