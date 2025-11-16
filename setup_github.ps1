# PowerShell скрипт для настройки GitHub репозитория

Write-Host "Настройка GitHub репозитория для TrueLiveBet" -ForegroundColor Green
Write-Host "=" * 60

# Проверка наличия remote
$remote = git remote -v
if ($remote) {
    Write-Host "Remote репозиторий уже настроен:" -ForegroundColor Yellow
    Write-Host $remote
    exit
}

Write-Host "`n1. Создай репозиторий на GitHub (через веб-интерфейс)" -ForegroundColor Cyan
Write-Host "   https://github.com/new" -ForegroundColor Gray
Write-Host "   Название: TrueLiveBet (или любое другое)" -ForegroundColor Gray
Write-Host "   Тип: Private (рекомендуется)" -ForegroundColor Gray

Write-Host "`n2. После создания репозитория, введи URL:" -ForegroundColor Cyan
$repoUrl = Read-Host "URL репозитория (например: https://github.com/username/TrueLiveBet.git)"

if ($repoUrl) {
    Write-Host "`nПодключение к remote репозиторию..." -ForegroundColor Yellow
    git remote add origin $repoUrl
    
    Write-Host "Переименование ветки в main..." -ForegroundColor Yellow
    git branch -M main
    
    Write-Host "`nГотово! Теперь можно отправить код:" -ForegroundColor Green
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
} else {
    Write-Host "`nОтменено. Можно выполнить вручную:" -ForegroundColor Yellow
    Write-Host "  git remote add origin <URL>" -ForegroundColor Gray
    Write-Host "  git branch -M main" -ForegroundColor Gray
    Write-Host "  git push -u origin main" -ForegroundColor Gray
}

