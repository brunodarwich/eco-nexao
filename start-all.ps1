# Script de Inicialização Completa do ECOconexão

Write-Host "Iniciando servidores (App Web, API Django, Admin e Streamlit)..." -ForegroundColor Green

$projectDir = "C:\Users\Bruno\Downloads\eco-nexao"

Start-Process powershell -WorkingDirectory $projectDir -ArgumentList "-NoExit -Command pnpm dev:web"
Start-Process powershell -WorkingDirectory $projectDir -ArgumentList "-NoExit -Command pnpm dev:api"
Start-Process powershell -WorkingDirectory $projectDir -ArgumentList "-NoExit -Command pnpm dev:admin"
Start-Process powershell -WorkingDirectory $projectDir -ArgumentList "-NoExit -Command pnpm dev:dashboard"

Write-Host "Aguardando 4 segundos para a inicializacao dos servidores..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

Write-Host "Abrindo guias do Chrome..." -ForegroundColor Cyan
Start-Process chrome "http://localhost:3000 http://localhost:3001 http://localhost:8000 http://localhost:8501"
