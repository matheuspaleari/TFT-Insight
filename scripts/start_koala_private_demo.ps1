param(
    [string]$ProjectRoot = "",
    [string]$VenvActivate = "",
    [int]$ApiPort = 8000,
    [int]$StreamlitPort = 8501
)

$ErrorActionPreference = "Stop"

Write-Host "==============================================================="
Write-Host "TFT INSIGHT / ROADMAP 25.1A - KOALA PRIVATE DEMO"
Write-Host "==============================================================="

# ----------------------------------------------------------------------
# Descobre automaticamente a raiz do projeto.
#
# Estrutura esperada:
#
# TFT-Insight/
#   scripts/
#     start_koala_private_demo.ps1
# ----------------------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {

    $ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

    $ProjectRoot = Split-Path -Parent $ScriptDirectory
}

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)

Write-Host ""
Write-Host "Projeto:"
Write-Host "  $ProjectRoot"

if (-not (Test-Path $ProjectRoot -PathType Container)) {
    throw "Projeto nao encontrado: $ProjectRoot"
}

# ----------------------------------------------------------------------
# Localiza o ambiente virtual.
#
# Prioridade:
#
# 1. Caminho informado via parametro
# 2. .venv dentro do proprio projeto
# 3. Ambiente virtual ja ativo no PowerShell
# ----------------------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($VenvActivate)) {

    $LocalVenvActivate = Join-Path `
        $ProjectRoot `
        ".venv\Scripts\Activate.ps1"

    if (Test-Path $LocalVenvActivate) {

        $VenvActivate = $LocalVenvActivate

    }
    elseif ($env:VIRTUAL_ENV) {

        $ActiveVenvActivate = Join-Path `
            $env:VIRTUAL_ENV `
            "Scripts\Activate.ps1"

        if (Test-Path $ActiveVenvActivate) {
            $VenvActivate = $ActiveVenvActivate
        }
    }
}

if ([string]::IsNullOrWhiteSpace($VenvActivate)) {

    throw @"
Nenhum ambiente virtual foi encontrado.

Opcoes:

1. Crie .venv dentro do projeto.

ou

2. Ative seu ambiente virtual antes de executar este script.

ou

3. Informe manualmente:

-VenvActivate "C:\caminho\venv\Scripts\Activate.ps1"
"@
}

if (-not (Test-Path $VenvActivate -PathType Leaf)) {
    throw "Venv nao encontrado: $VenvActivate"
}

Write-Host ""
Write-Host "Ambiente virtual:"
Write-Host "  $VenvActivate"

# ----------------------------------------------------------------------
# Cloudflared
# ----------------------------------------------------------------------

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {

    Write-Host ""
    Write-Host "ERRO: cloudflared nao encontrado."
    Write-Host "Instale o cloudflared pelo instalador oficial da Cloudflare e rode novamente."

    exit 1
}

# ----------------------------------------------------------------------
# Comandos
# ----------------------------------------------------------------------

$apiCommand = @"
Set-Location '$ProjectRoot'
& '$VenvActivate'
`$env:PYTHONDONTWRITEBYTECODE='1'
python run_api.py
"@

$uiCommand = @"
Set-Location '$ProjectRoot'
& '$VenvActivate'
`$env:PYTHONDONTWRITEBYTECODE='1'
python scripts\run_partner_platform.py
"@

# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------

Write-Host ""
Write-Host "[1/3] Abrindo API..."

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $apiCommand
)

Start-Sleep -Seconds 4

# ----------------------------------------------------------------------
# Streamlit
# ----------------------------------------------------------------------

Write-Host "[2/3] Abrindo Streamlit..."

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $uiCommand
)

Write-Host ""
Write-Host "Aguardando Streamlit subir..."

Start-Sleep -Seconds 8

# ----------------------------------------------------------------------
# Cloudflare Quick Tunnel
# ----------------------------------------------------------------------

Write-Host "[3/3] Abrindo Cloudflare Quick Tunnel..."

Write-Host ""
Write-Host "IMPORTANTE:"
Write-Host "- O link *.trycloudflare.com e temporario."
Write-Host "- Compartilhe somente durante o teste."
Write-Host "- Seu PC precisa continuar ligado."
Write-Host "- Ctrl+C nesta janela encerra o link publico."
Write-Host ""
Write-Host "Quando aparecer a URL do Quick Tunnel, copie e envie ao testador."
Write-Host ""

cloudflared tunnel --url "http://127.0.0.1:$StreamlitPort"