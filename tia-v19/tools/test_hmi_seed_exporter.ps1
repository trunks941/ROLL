param([string]$Exporter = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Export-HmiSeed.ps1'))
$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Exporter, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Exporter parsing failed.' }
foreach ($name in @('Get-HmiSeedInventory', 'Get-HmiSeedRequirements')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    if ($null -eq $definition) { throw "Missing exporter function: $name" }
    . ([scriptblock]::Create($definition.Extent.Text))
}
# Guard the exporter body against engineering mutations. The five read/export
# functions loaded from the builder are an explicit whitelist in the exporter.
$forbidden = @($ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and
    $node.Member.Value -in @('Save', 'SaveAs', 'Import', 'Delete', 'SetAttribute', 'SetAttributes', 'Compile', 'Create', 'CreateWithItem', 'GenerateBlocksFromSource', 'Download', 'Close') -and
    -not ($node.Static -and $node.Member.Value -eq 'Create' -and $node.Expression.TypeName.FullName -in @('scriptblock', 'System.Management.Automation.ScriptBlock'))
}, $true))
if ($forbidden.Count -gt 0) { throw 'Exporter contains an engineering mutation call.' }
$screen1 = [pscustomobject]@{ Name = 'WZOR_ROLL'; ScreenItems = @('text', 'button', 'io', 'alarm') }
$screen2 = [pscustomobject]@{ Name = 'Nested'; ScreenItems = @('text') }
$table1 = [pscustomobject]@{ Name = 'Default'; Tags = @('Bool', 'Int') }
$table2 = [pscustomobject]@{ Name = 'Nested'; Tags = @('Bool') }
$hmi = [pscustomobject]@{
    ScreenFolder = [pscustomobject]@{ Screens = @($screen1); Folders = @([pscustomobject]@{ Name = 'Inner'; Screens = @($screen2); Folders = @() }) }
    TagFolder = [pscustomobject]@{ TagTables = @($table1); Folders = @([pscustomobject]@{ Name = 'Inner'; TagTables = @($table2); Folders = @() }) }
    Connections = @([pscustomobject]@{ Name = 'ROLL_PLC' })
    Cycles = @([pscustomobject]@{ Name = '1s' })
}
$inventory = @(Get-HmiSeedInventory $hmi)
if ($inventory.Count -ne 6) { throw 'Nested inventory count mismatch.' }
if (@($inventory | Where-Object { $_.Kind -eq 'Screen' }).Count -ne 2) { throw 'Nested screen missing.' }
if (@($inventory | Where-Object { $_.Kind -eq 'TagTable' }).Count -ne 2) { throw 'Nested tag table missing.' }
if (@($inventory | Where-Object { $_.Folder -eq 'ScreenFolder/Inner' }).Count -ne 1) { throw 'Nested path not preserved.' }
$goodScreens = @([pscustomobject]@{ itemCount = 4 })
$goodTables = @([pscustomobject]@{ tagCount = 3 })
if (@(Get-HmiSeedRequirements $goodScreens $goodTables 1).Count -ne 0) { throw 'Complete sample rejected.' }
if (@(Get-HmiSeedRequirements @() @() 0).Count -ne 4) { throw 'Empty sample not diagnosed.' }
if (@(Get-HmiSeedRequirements @([pscustomobject]@{ itemCount = 1 }) $goodTables 1).Count -ne 1) { throw 'Missing controls not diagnosed.' }
if (@(Get-HmiSeedRequirements $goodScreens @([pscustomobject]@{ tagCount = 2 }) 1).Count -ne 1) { throw 'Missing tag not diagnosed.' }
$result = [ordered]@{
    success = $true; inventoryScenarios = 1; requirementScenarios = 4
    mutationCallGuardPassed = $true; parserVersion = $PSVersionTable.PSVersion.ToString()
    scope = 'nested HMI inventory and template completeness diagnostics on data doubles; exporter AST mutation-call guard'
    nativeTiaExecuted = $false; nativeHmiExportVerified = $false
    exporterSHA256 = (Get-FileHash -LiteralPath $Exporter -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'reports/hmi-seed-exporter-tests.json') -Encoding UTF8
Write-Host 'Passed: nested inventory, 4 requirement scenarios and exporter mutation-call guard. Native TIA was not executed.'
