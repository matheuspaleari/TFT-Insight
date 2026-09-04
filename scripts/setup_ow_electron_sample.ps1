param(
  [string]$Destination = "$env:USERPROFILE\Desktop\TFT-Insight-OW-Electron"
)
$ErrorActionPreference="Stop"
Write-Host "=== TFT Insight / Roadmap 25.0R - OW-Electron Bootstrap ==="
Write-Host "Node:" (node -v)
Write-Host "npm :" (npm -v)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git nao encontrado. Instale Git for Windows antes de continuar."
}
if (Test-Path $Destination) {
  throw "Destino ja existe: $Destination"
}
git clone https://github.com/overwolf/ow-electron-packages-sample.git $Destination
Set-Location $Destination
npm install
Write-Host ""
Write-Host "Projeto oficial clonado e dependencias instaladas."
Write-Host "Destino: $Destination"
Write-Host ""
Write-Host "PROXIMO PASSO:"
Write-Host "1) Nao coloque sua API key em arquivo versionado."
Write-Host '2) Configure OW_DEV_KEY OU OW_CLI_EMAIL + OW_CLI_API_KEY somente na sessao PowerShell.'
Write-Host "3) Depois integre o coletor TFT do pacote 25.0Q/25.0R."
