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
$result = [ordered]@{
    success = $true; cases = $cases.Count; parserVersion = $PSVersionTable.PSVersion.ToString()
    scope = 'diagnostic classification of Siemens group error and unrelated failures'
    nativeWindowsGroupMembershipTested = $false
    nativeTiaExecuted = $false
    builderSHA256 = (Get-FileHash -LiteralPath $Builder -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'reports/builder-diagnostics-tests.json') -Encoding UTF8
Write-Host "Diagnostic classification: $($cases.Count) cases passed."
