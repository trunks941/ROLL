param([string]$Builder = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Build-Roll.ps1'))
$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Builder, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Builder parsing failed.' }
$definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-OpennessDiagnostic' }, $true)
if ($null -eq $definition) { throw 'Diagnostic function not found.' }
# Load only the pure diagnostic function; do not execute the project builder.
. ([scriptblock]::Create($definition.Extent.Text))
$generationFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-RollSourceGeneration' }, $true)
if ($null -eq $generationFunction) { throw 'Source generation function not found.' }
. ([scriptblock]::Create($generationFunction.Extent.Text))
$cases = @(
    @{ text = "Siemens.Engineering.EngineeringSecurityException: Security error. Owner of this process is not member of the windows group 'Siemens TIA Openness'. Please contact your administrator."; expected = 'windows_openness_group_membership' },
    @{ text = "Owner is not a member of the windows group 'Siemens TIA Openness'."; expected = 'windows_openness_group_membership' },
    @{ text = 'Security error. The application was denied access to TIA Openness.'; expected = $null },
    @{ text = 'CPU is absent from the installed V19 catalog.'; expected = $null },
    @{ text = 'Compiler error: invalid SCL statement.'; expected = $null }
)
foreach ($case in $cases) {
    $actual = Get-OpennessDiagnostic $case.text
    if ($null -eq $case.expected) {
        if ($null -ne $actual) { throw "Incorrect group diagnosis: $($case.text)" }
    } else {
        if ($null -eq $actual -or $actual.Code -ne $case.expected -or $actual.RequiredGroup -ne 'Siemens TIA Openness') { throw 'Membership diagnostic mismatch.' }
        if ($actual.NextAction -notmatch 'Sign out of Windows') { throw 'Missing token refresh instruction.' }
    }
}
$report = [ordered]@{ sourceGenerationSucceeded = $false; sourceGenerationError = $null; errors = @() }
$goodSource = New-Object PSObject
$goodSource | Add-Member -MemberType ScriptMethod -Name GenerateBlocksFromSource -Value { return @('SDK output must be suppressed') }
$ok = Invoke-RollSourceGeneration $goodSource
if ($ok -isnot [bool] -or -not $ok -or -not $report.sourceGenerationSucceeded -or $report.errors.Count -ne 0) { throw 'Successful generation result was not captured correctly.' }
$badSource = New-Object PSObject
$badSource | Add-Member -MemberType ScriptMethod -Name GenerateBlocksFromSource -Value { throw 'An error occurred during code generation. Row 000029: Syntax error: Timer is invalid.' }
$ok = Invoke-RollSourceGeneration $badSource
if ($ok -isnot [bool] -or $ok -or $report.sourceGenerationSucceeded -or $report.errors.Count -ne 1 -or $report.sourceGenerationError -notmatch 'Row 000029') { throw 'Failed source generation was not preserved as a failure.' }
$result = [ordered]@{
    success = $true; cases = $cases.Count; parserVersion = $PSVersionTable.PSVersion.ToString()
    sourceGenerationCases = 2
    scope = 'diagnostic classification and success/failure handling of source generation with an API double'
    nativeWindowsGroupMembershipTested = $false
    nativeTiaExecuted = $false
    builderSHA256 = (Get-FileHash -LiteralPath $Builder -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'reports/builder-diagnostics-tests.json') -Encoding UTF8
Write-Host "Diagnostic classification: $($cases.Count) cases passed."
Write-Host 'Source generation result handling: 2 cases passed; native Siemens SDK was not executed.'
