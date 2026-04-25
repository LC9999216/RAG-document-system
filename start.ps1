$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "未找到项目虚拟环境解释器: $pythonPath"
}

$port = 8001
$tmpDir = Join-Path $projectRoot ".tmp"
$stdoutLog = Join-Path $projectRoot "uvicorn_stdout.log"
$stderrLog = Join-Path $projectRoot "uvicorn_stderr.log"

New-Item -ItemType Directory -Force $tmpDir | Out-Null

$env:TEMP = $tmpDir
$env:TMP = $tmpDir
$env:PYTHONIOENCODING = "utf-8"

Remove-Item Env:HF_HOME -ErrorAction SilentlyContinue
Remove-Item Env:HUGGINGFACE_HUB_CACHE -ErrorAction SilentlyContinue

$existing = netstat -ano | Select-String ":$port\s+.*LISTENING\s+(\d+)$"
if ($existing) {
    $pids = $existing | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique
    foreach ($pid in $pids) {
        if ($pid -match '^\d+$') {
            Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "RAG 服务启动中..."
Write-Host "地址: http://127.0.0.1:$port/"
Write-Host "文档: http://127.0.0.1:$port/docs"
Write-Host "临时目录: $tmpDir"
Write-Host "标准输出日志: $stdoutLog"
Write-Host "错误日志: $stderrLog"

& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port $port
