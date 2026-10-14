param([string]$Builder = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Build-Roll.ps1'))
$ErrorActionPreference = 'Stop'
$parseTokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($Builder, [ref]$parseTokens, [ref]$parseErrors) | Out-Null
foreach ($errorItem in $parseErrors) {
    Write-Host "Line $($errorItem.Extent.StartLineNumber): $($errorItem.Message)"
}
$result = [ordered]@{
    parserPassed = $parseErrors.Count -eq 0
    parserVersion = $PSVersionTable.PSVersion.ToString()
    windowsPowerShell51Executed = $false
    tiaOpennessExecuted = $false
    scriptSHA256 = (Get-FileHash -LiteralPath $Builder -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'reports/powershell-checks.json') -Encoding UTF8
if ($parseErrors.Count -gt 0) { exit 1 }
Write-Host 'PowerShell parser: OK; Siemens/Windows execution remains untested.'
