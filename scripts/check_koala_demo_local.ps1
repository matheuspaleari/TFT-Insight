param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [string]$StreamlitUrl = "http://127.0.0.1:8501"
)

Write-Host "==============================================================="
Write-Host "TFT INSIGHT / ROADMAP 25.1A - PRE-DEMO CHECK"
Write-Host "==============================================================="

function Test-Url {
    param([string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        Write-Host "[OK] $Url -> HTTP $($r.StatusCode)"
        return $true
    }
    catch {
        Write-Host "[ERRO] $Url -> $($_.Exception.Message)"
        return $false
    }
}

$api = Test-Url $ApiUrl
$ui = Test-Url $StreamlitUrl

if ($api -and $ui) {
    Write-Host ""
    Write-Host "API e Streamlit respondendo localmente."
    exit 0
}

Write-Host ""
Write-Host "Algum servico ainda nao respondeu. Confira os terminais da API/Streamlit."
exit 1
