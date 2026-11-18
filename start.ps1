# PPT Component Studio 启动脚本 (UTF-8 PowerShell)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  PPT Component Studio - 元件化演示文稿设计器" -ForegroundColor Yellow
Write-Host "  Web 编辑器地址: http://127.0.0.1:8765" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8765"
python server.py
