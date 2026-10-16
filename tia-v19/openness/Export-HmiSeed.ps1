param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'ROLL_TIA_V19'),
    [string]$ApiPath = 'C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll',
    [string]$ProjectName = '',
    [string]$HmiName = 'ROLL_TP900'
)

# Reads an already open offline project. Does not save, import, create engineering
# objects, compile, connect online or download to a device.
$ErrorActionPreference = 'Stop'
$runDirectory = Join-Path $OutputDirectory ('ROLL_HMI_WZOR_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6))
[IO.Directory]::CreateDirectory($runDirectory) | Out-Null
$report = [ordered]@{
    status = 'starting'; project = $null; hmi = $null
    screens = @(); tagTables = @(); connectionCount = 0; connectionReferenceNames = @()
    requirementsMissing = @(); exports = @(); warnings = @(); errors = @()
    projectSavedByExporter = $false; engineeringObjectsChanged = $false
    nativeBindingsValidated = $false; runtimeSettingsValidated = $false
    downloadsPerformed = $false; reportArchive = $null
}
$tia = $null
$exitCode = 1

function Get-HmiSeedInventory($Hmi) {
    $objects = @()
    foreach ($spec in @(
        @{ Root = 'ScreenFolder'; Collection = 'Screens'; Kind = 'Screen' },
        @{ Root = 'TagFolder'; Collection = 'TagTables'; Kind = 'TagTable' },
        @{ Root = 'VBScriptFolder'; Collection = 'VBScripts'; Kind = 'VBScript' },
        @{ Root = 'ScreenTemplateFolder'; Collection = 'ScreenTemplates'; Kind = 'ScreenTemplate' },
        @{ Root = 'ScreenPopupFolder'; Collection = 'ScreenPopups'; Kind = 'ScreenPopup' }
    )) {
        if ($null -eq $Hmi.PSObject.Properties[$spec.Root]) { continue }
        $queue = New-Object 'System.Collections.Generic.Queue[object]'
        $queue.Enqueue([pscustomobject]@{ Object = $Hmi.($spec.Root); Path = $spec.Root })
        while ($queue.Count -gt 0) {
            $folder = $queue.Dequeue()
            if ($null -eq $folder.Object) { continue }
            if ($null -ne $folder.Object.PSObject.Properties[$spec.Collection]) {
                foreach ($item in $folder.Object.($spec.Collection)) {
                    $objects += [pscustomobject]@{ Kind = $spec.Kind; Folder = $folder.Path; Name = [string]$item.Name; NativeObject = $item }
                }
            }
            if ($null -ne $folder.Object.PSObject.Properties['Folders']) {
                foreach ($child in $folder.Object.Folders) { $queue.Enqueue([pscustomobject]@{ Object = $child; Path = $folder.Path + '/' + $child.Name }) }
            }
        }
    }
    foreach ($name in @('Connections', 'Cycles', 'TextLists', 'GraphicLists')) {
        if ($null -eq $Hmi.PSObject.Properties[$name]) { continue }
        foreach ($item in $Hmi.$name) {
            $objects += [pscustomobject]@{ Kind = $name; Folder = $name; Name = [string]$item.Name; NativeObject = $item }
        }
    }
    return $objects
}

function Get-HmiSeedScreenSummary([string]$FileName) {
    # Comfort Screen exposes Name through Openness, while controls reside in
    # ScreenLayer/ObjectList in its XML. A missing ScreenItems API property is
    # not evidence of an empty screen.
    $xml = New-Object Xml.XmlDocument
    $xml.Load($FileName)
    $screen = $xml.SelectSingleNode("//*[local-name()='Hmi.Screen.Screen']")
    if ($null -eq $screen) { throw 'Export contains no native Comfort screen.' }
    $items = @($screen.SelectNodes(".//*[@CompositionName='ScreenItems']"))
    $unboundIo = @()
    foreach ($item in $items) {
        if ($item.LocalName -eq 'Hmi.Screen.IOField' -and $item.SelectNodes(".//*[local-name()='LinkList']/*/*[local-name()='Name']").Count -eq 0) {
            $unboundIo += $item.SelectSingleNode("./*[local-name()='AttributeList']/*[local-name()='ObjectName']").InnerText
        }
    }
    return [pscustomobject]@{
        name = $screen.SelectSingleNode("./*[local-name()='AttributeList']/*[local-name()='Name']").InnerText
        itemCount = $items.Count; itemTypes = @($items | ForEach-Object { $_.LocalName })
        unboundIoFields = $unboundIo; itemCountSource = 'native_screen_xml'
    }
}

function Get-HmiSeedConnectionReferences([string]$FileName) {
    $xml = New-Object Xml.XmlDocument
    $xml.Load($FileName)
    return @($xml.SelectNodes("//*[local-name()='Hmi.Tag.Tag']/*[local-name()='LinkList']/*[local-name()='Connection']/*[local-name()='Name']") | ForEach-Object { $_.InnerText } | Sort-Object -Unique)
}

function Get-HmiSeedRequirements($Screens, $TagTables, [int]$ConnectionCount, $ConnectionReferences = @()) {
    $missing = @()
    if (@($Screens).Count -eq 0) { $missing += 'No screen. Add WZOR_ROLL in the TIA editor.' }
    $itemCount = 0
    foreach ($screen in $Screens) { $itemCount += [int]$screen.itemCount }
    if ($itemCount -lt 4) { $missing += 'Fewer than four screen objects. Add a text field, button, numeric I/O field and alarm view.' }
    $types = @($Screens | ForEach-Object { $_.itemTypes } | Where-Object { $_ })
    if ($types.Count -gt 0) {
        foreach ($required in @('Hmi.Screen.TextField', 'Hmi.Screen.Button', 'Hmi.Screen.IOField', 'Hmi.Screen.AlarmView')) {
            if ($required -notin $types) { $missing += "Missing native control: $required." }
        }
    }
    foreach ($screen in $Screens) {
        foreach ($field in $screen.unboundIoFields) { $missing += "I/O field '$field' has no exported link. Assign its process tag to WzorLiczba in TIA." }
    }
    $tagCount = 0
    foreach ($table in $TagTables) { $tagCount += [int]$table.tagCount }
    if ($tagCount -lt 3) { $missing += 'Fewer than three HMI tags. See HMI_WZOR.md.' }
    if ($ConnectionCount -lt 1 -and @($ConnectionReferences).Count -eq 0) { $missing += 'No exported HMI connection or connection reference. Check ROLL_PLC in the TIA project.' }
    return $missing
}

function Export-SeedObject($Entry, [int]$Index) {
    $baseName = ('{0:D3}_{1}_{2}' -f $Index, $Entry.Kind, ($Entry.Name -replace '[^\p{L}\p{Nd}_-]', '_'))
    Export-ApiDescription $Entry.NativeObject ($baseName + '-api.json')
    try {
        $path = Join-Path $runDirectory ($baseName + '.xml')
        $Entry.NativeObject.Export((New-Object IO.FileInfo($path)), [Siemens.Engineering.ExportOptions]::WithDefaults)
        $report.exports += [ordered]@{ kind = $Entry.Kind; folder = $Entry.Folder; name = $Entry.Name; file = $baseName + '.xml'; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
        return $path
    } catch { $report.warnings += "Export $($Entry.Kind)/$($Entry.Name): $($_.Exception.Message)" }
}

try {
    if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit Windows PowerShell.' }
    if (-not (Test-Path -LiteralPath $ApiPath)) { throw "Missing TIA V19 API: $ApiPath" }
    # Load only these read/export function definitions, never the builder body.
    $tokens = $null
    $parseErrors = $null
    $builderAst = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root 'openness\Build-Roll.ps1'), [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count -gt 0) { throw 'Build-Roll.ps1 cannot be parsed.' }
    foreach ($functionName in @('Get-Service', 'Find-Software', 'Export-ApiDescription', 'Get-EngineeringCompositionMethod', 'Get-EngineeringCreationInfos')) {
        $definition = $builderAst.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName }, $true)
        if ($null -eq $definition) { throw "Missing read/export helper: $functionName" }
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    [Reflection.Assembly]::LoadFrom($ApiPath) | Out-Null
    foreach ($name in @('Siemens.Engineering.Hmi.dll', 'Siemens.Engineering.HW.dll')) {
        $extra = Join-Path (Split-Path -Parent $ApiPath) $name
        if (Test-Path -LiteralPath $extra) { [Reflection.Assembly]::LoadFrom($extra) | Out-Null }
    }
    $processes = @([Siemens.Engineering.TiaPortal]::GetProcesses() | Where-Object { $null -ne $_.ProjectPath })
    if ($ProjectName) {
        $processes = @($processes | Where-Object { [IO.Path]::GetFileNameWithoutExtension([string]$_.ProjectPath) -eq $ProjectName })
    }
    if ($processes.Count -eq 0) { throw 'Open and save the ROLL project in TIA V19, leave it open, then run this exporter.' }
    if ($processes.Count -gt 1) {
        Write-Host 'Wybierz otwarty projekt do eksportu:'
        for ($i = 0; $i -lt $processes.Count; $i++) { Write-Host ("{0}: {1}" -f ($i + 1), [IO.Path]::GetFileName([string]$processes[$i].ProjectPath)) }
        $choice = 0
        if (-not [int]::TryParse((Read-Host 'Numer projektu'), [ref]$choice) -or $choice -lt 1 -or $choice -gt $processes.Count) { throw 'Invalid project choice.' }
        $processes = @($processes[$choice - 1])
    }
    $tia = $processes[0].Attach()
    $projects = @($tia.Projects)
    if ($projects.Count -ne 1) { throw 'Expected one open project in the selected TIA instance.' }
    $project = $projects[0]
    $report.project = [string]$project.Name
    Export-ApiDescription $project 'project-api.json'
    $targets = @()
    foreach ($device in $project.Devices) {
        try {
            $software = Find-Software $device
            if ($software.GetType().FullName -eq 'Siemens.Engineering.Hmi.HmiTarget') { $targets += $software }
        } catch { $report.warnings += 'Device software read: ' + $_.Exception.Message }
    }
    $matches = @($targets | Where-Object { $_.Name -eq $HmiName })
    if ($matches.Count -eq 1) { $hmi = $matches[0] }
    elseif ($targets.Count -eq 1) { $hmi = $targets[0] }
    else { throw "Cannot select one Comfort HMI target; specify -HmiName. Found: $($targets.Count)." }
    $report.hmi = [string]$hmi.Name
    Export-ApiDescription $hmi 'hmi-api.json'
    Export-ApiDescription $hmi.Connections 'hmi-connections-api.json'
    $inventory = @(Get-HmiSeedInventory $hmi)
    $index = 0
    foreach ($entry in $inventory) {
        $index++
        $exportPath = Export-SeedObject $entry $index
        if ($entry.Kind -eq 'Screen') {
            if ($exportPath) {
                $summary = Get-HmiSeedScreenSummary $exportPath
                $report.screens += [ordered]@{ name = $entry.Name; folder = $entry.Folder; itemCount = $summary.itemCount; itemTypes = $summary.itemTypes; unboundIoFields = $summary.unboundIoFields; itemCountSource = $summary.itemCountSource }
            }
        } elseif ($entry.Kind -eq 'TagTable') {
            $report.tagTables += [ordered]@{ name = $entry.Name; folder = $entry.Folder; tagCount = @($entry.NativeObject.Tags).Count }
            $tagIndex = 0
            foreach ($tag in $entry.NativeObject.Tags) { $tagIndex++; Export-ApiDescription $tag ('table-' + $index + '-tag-' + $tagIndex + '-api.json') }
            if ($exportPath) { $report.connectionReferenceNames += @(Get-HmiSeedConnectionReferences $exportPath) }
        } elseif ($entry.Kind -eq 'Connections') { $report.connectionCount++ }
    }
    $report.connectionReferenceNames = @($report.connectionReferenceNames | Sort-Object -Unique)
    if ($report.connectionCount -eq 0 -and $report.connectionReferenceNames.Count -gt 0) {
        $report.warnings += 'Tags reference HMI connections, but the API exported no connection definitions. Preserve the configured connection in the existing project. This does not prove the connection is absent.'
    }
    $report.requirementsMissing = @(Get-HmiSeedRequirements $report.screens $report.tagTables $report.connectionCount $report.connectionReferenceNames)
    if (@($report.exports | Where-Object { $_.kind -eq 'Screen' }).Count -eq 0) { $report.requirementsMissing += 'No screen XML was exported. See warnings.' }
    if (@($report.exports | Where-Object { $_.kind -eq 'TagTable' }).Count -eq 0) { $report.requirementsMissing += 'No tag table XML was exported. See warnings.' }
    if ($report.connectionCount -gt 0 -and @($report.exports | Where-Object { $_.kind -eq 'Connections' }).Count -eq 0) { $report.requirementsMissing += 'Connection objects exist, but their XML export failed. See warnings.' }
    $report.status = 'exported'
    $exitCode = 0
    if ($report.requirementsMissing.Count -gt 0) { $report.status = 'exported_with_gaps'; $exitCode = 2 }
} catch {
    $report.status = 'blocked'
    $report.errors += $_.Exception.ToString()
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    $report.finished = (Get-Date).ToString('o')
    if ($null -ne $tia) { try { $tia.Dispose() } catch { $report.warnings += 'TIA detach: ' + $_.Exception.Message } }
    $report.reportArchive = $runDirectory + '_eksport.zip'
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runDirectory 'hmi-seed-report.json') -Encoding UTF8
    try { Compress-Archive -Path (Join-Path $runDirectory '*') -DestinationPath $report.reportArchive }
    catch {
        $report.status = 'archive_failed'
        $report.errors += 'ZIP: ' + $_.Exception.Message
        $report.reportArchive = $null
        $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runDirectory 'hmi-seed-report.json') -Encoding UTF8
        Write-Host ('ZIP: ' + $_.Exception.Message)
        $exitCode = 1
    }
    Write-Host ('Eksport: ' + $report.status)
    foreach ($message in $report.requirementsMissing) { Write-Host $message -ForegroundColor Yellow }
    Write-Host ('Pliki: ' + $runDirectory)
    Write-Host ('Przeslij paczke: ' + $report.reportArchive)
}
exit $exitCode
