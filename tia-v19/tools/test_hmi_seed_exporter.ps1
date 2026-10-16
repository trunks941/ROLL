param([string]$Exporter = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Export-HmiSeed.ps1'))
$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Exporter, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Exporter parsing failed.' }
foreach ($name in @('Get-HmiSeedInventory', 'Get-HmiSeedRequirements', 'Get-HmiSeedScreenSummary', 'Get-HmiSeedConnectionReferences')) {
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
$seed = Join-Path (Split-Path -Parent $PSScriptRoot) 'hmi/seed'
$summary = Get-HmiSeedScreenSummary (Join-Path $seed 'WZOR_ROLL-unbound-regression.xml')
if ($summary.itemCount -ne 4 -or $summary.itemCountSource -ne 'native_screen_xml') { throw 'Actual layered screen controls were not counted.' }
if ($summary.itemTypes -notcontains 'Hmi.Screen.Circle' -or $summary.itemTypes -contains 'Hmi.Screen.AlarmView') { throw 'Actual control types were not identified.' }
if ($summary.unboundIoFields.Count -ne 1 -or $summary.unboundIoFields[0] -ne 'I/O field_1') { throw 'Unbound native I/O field was not detected.' }
$references = @(Get-HmiSeedConnectionReferences (Join-Path $seed 'tags.xml'))
if ($references.Count -ne 1 -or $references[0] -ne 'ROLL_PLC') { throw 'Connection reference deduplication failed.' }
$gaps = @(Get-HmiSeedRequirements @($summary) $goodTables 0 $references)
if ($gaps.Count -ne 1 -or @($gaps | Where-Object { $_ -like '*WzorLiczba*' }).Count -ne 1) { throw 'Old native sample must identify the I/O assignment gap; the alarm view and connection must not be false blockers.' }
$bound = Get-HmiSeedScreenSummary (Join-Path $seed 'WZOR_ROLL.xml')
if ($bound.itemCount -ne 4 -or $bound.unboundIoFields.Count -ne 0) { throw 'Latest native sample must expose four controls and a bound I/O field.' }
if (@(Get-HmiSeedRequirements @($bound) $goodTables 0 $references).Count -ne 0) { throw 'Latest sample must be usable without requiring re-export of the alarm view.' }
$result = [ordered]@{
    success = $true; inventoryScenarios = 1; requirementScenarios = 4
    nativeXmlFixtureScenarios = 4
    mutationCallGuardPassed = $true; parserVersion = $PSVersionTable.PSVersion.ToString()
    scope = 'nested HMI inventory and completeness diagnostics on data doubles; real native XML layered controls, unbound IO and connection-reference regression; exporter AST mutation-call guard'
    nativeTiaExecuted = $false; nativeHmiExportVerified = $false
    exporterSHA256 = (Get-FileHash -LiteralPath $Exporter -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'reports/hmi-seed-exporter-tests.json') -Encoding UTF8
Write-Host 'Passed: nested inventory, 4 requirement scenarios, 4 native XML fixture scenarios and exporter mutation-call guard. Native TIA was not executed.'
