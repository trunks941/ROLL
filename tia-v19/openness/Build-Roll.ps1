param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'ROLL_TIA_V19'),
    [string]$ApiPath = 'C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll'
)

# Windows PowerShell 5.1, x64, with STEP 7 Professional and WinCC Advanced V19.
# Creates a NEW offline project. No PLC/HMI download or online connection.
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root)
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$projectName = 'ROLL_' + $stamp + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
$runDirectory = Join-Path $OutputDirectory $projectName
[IO.Directory]::CreateDirectory($runDirectory) | Out-Null
$report = [ordered]@{
    started = (Get-Date).ToString('o'); project = $projectName
    status = 'starting'; phase = 'prerequisites'; projectFile = $null
    cpuCatalogIdentifier = $null; deliveredFirmwareVerified = $false
    hmiCatalogIdentifier = $null; nativeScreens = @(); hmiFullyConfigured = $false
    physicalIoConfigured = $false; hardwareIoValidated = $false
    plcCompilation = $null; errors = @(); warnings = @(); catalogAttempts = @()
    sourceInventoryComplete = $false; sourceInventoryMissing = @()
    retentionConfigured = $false; retentionChecks = @(); initialPlcCompilation = $null
    machineTested = $false; downloadsPerformed = $false
    reportArchive = $null
}
$tia = $null
$project = $null
$exitCode = 1

function Save-Report {
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runDirectory 'build-report.json') -Encoding UTF8
}

function Read-BlockNumber($Block) {
    if ($null -ne $Block.PSObject.Properties['Number']) { return [int]$Block.Number }
    try { return [int]$Block.GetAttribute('Number') } catch { return -1 }
}

function Get-Service($Object, [string]$TypeName) {
    # GetService<T>() can be an explicit interface implementation.
    $wanted = [Siemens.Engineering.TiaPortal].Assembly.GetType($TypeName)
    if ($null -eq $wanted) {
        foreach ($assembly in [AppDomain]::CurrentDomain.GetAssemblies()) {
            $wanted = $assembly.GetType($TypeName)
            if ($null -ne $wanted) { break }
        }
    }
    if ($null -eq $wanted) { throw "API type not found: $TypeName" }
    $provider = [Siemens.Engineering.IEngineeringServiceProvider]
    if (-not $provider.IsInstanceOfType($Object)) { return $null }
    $method = $provider.GetMethods() | Where-Object { $_.Name -eq 'GetService' -and $_.IsGenericMethodDefinition } | Select-Object -First 1
    if ($null -eq $method) { throw 'API GetService<T> method not found.' }
    return $method.MakeGenericMethod([Type[]]@($wanted)).Invoke($Object, @())
}

function Find-Software($Device) {
    $queue = New-Object 'System.Collections.Generic.Queue[object]'
    foreach ($item in $Device.DeviceItems) { $queue.Enqueue($item) }
    while ($queue.Count -gt 0) {
        $item = $queue.Dequeue()
        $container = Get-Service $item 'Siemens.Engineering.HW.Features.SoftwareContainer'
        if ($null -ne $container -and $null -ne $container.Software) { return $container.Software }
        foreach ($child in $item.DeviceItems) { $queue.Enqueue($child) }
    }
    throw "No engineering software found in device: $($Device.Name)"
}

function Create-Device($Project, $Identifiers, [string]$Name) {
    foreach ($identifier in $Identifiers) {
        try {
            $device = $Project.Devices.CreateWithItem($identifier, $Name, $Name + '_Station')
            $report.catalogAttempts += [ordered]@{ name = $Name; identifier = $identifier; created = $true }
            return @{ Device = $device; Identifier = $identifier }
        } catch {
            $report.catalogAttempts += [ordered]@{ name = $Name; identifier = $identifier; created = $false; message = $_.Exception.Message }
        }
    }
    throw "Device $Name is absent from the installed V19 catalog. See catalogAttempts in the report; install the appropriate Siemens update/HSP or choose the exact supported version locally."
}

function Compiler-Messages($Result) {
    $messages = @()
    foreach ($message in $Result.Messages) {
        $messages += [ordered]@{ state = [string]$message.State; description = [string]$message.Description; path = [string]$message.Path }
        if ($null -ne $message.Messages) {
            $nested = [pscustomobject]@{ Messages = $message.Messages }
            $messages += @(Compiler-Messages $nested)
        }
    }
    return $messages
}

function Export-ApiDescription($Object, [string]$FileName) {
    if ($null -eq $Object) { return }
    $type = $Object.GetType()
    $description = [ordered]@{
        type = $type.FullName
        properties = @($type.GetProperties() | ForEach-Object { $_.Name + ' : ' + $_.PropertyType.FullName })
        methods = @($type.GetMethods() | Where-Object { $_.Name -in @('Create', 'Import', 'Export', 'GetAttribute', 'SetAttribute', 'GetAttributeInfos') } | ForEach-Object { $_.ToString() })
    }
    try { $description.attributes = @($Object.GetAttributeInfos() | ForEach-Object { @{ name = $_.Name; access = [string]$_.AccessMode } }) } catch { $description.attributeReadError = $_.Exception.Message }
    $description | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $runDirectory $FileName) -Encoding UTF8
}

function Configure-Retention($Plc, [string]$Directory) {
    $complete = $true
    foreach ($name in @('ROLL_State', 'ROLL_DB15', 'ROLL_DB19', 'ROLL_DB205', 'ROLL_Recipe1', 'ROLL_Recipe2')) {
        $check = [ordered]@{ block = $name; verified = $false; message = $null }
        try {
            $block = $Plc.BlockGroup.Blocks.Find($name)
            if ($null -eq $block) { throw "Missing DB: $name" }
            $before = Join-Path $Directory ($name + '-before-retention.xml')
            $block.Export((New-Object IO.FileInfo($before)), [Siemens.Engineering.ExportOptions]::WithDefaults)
            $xml = New-Object Xml.XmlDocument
            $xml.PreserveWhitespace = $true
            $xml.Load($before)
            $query = "//*[local-name()='Interface']/*[local-name()='Sections']/*[local-name()='Section' and @Name='Static']/*[local-name()='Member']"
            $members = @($xml.SelectNodes($query))
            if ($members.Count -eq 0) { throw 'Native DB export exposes no Static members; configure retention in TIA and provide its export.' }
            foreach ($member in $members) {
                if (-not $member.HasAttribute('Remanence') -or $member.GetAttribute('Remanence') -notin @('NonRetain', 'Retain')) {
                    throw 'Unknown native Remanence attribute; no guessed XML is imported.'
                }
                $member.SetAttribute('Remanence', 'Retain')
            }
            $edited = Join-Path $Directory ($name + '-retain-import.xml')
            $xml.Save($edited)
            $Plc.BlockGroup.Blocks.Import((New-Object IO.FileInfo($edited)), [Siemens.Engineering.ImportOptions]::Override) | Out-Null
            $after = Join-Path $Directory ($name + '-retention-check.xml')
            $block = $Plc.BlockGroup.Blocks.Find($name)
            $block.Export((New-Object IO.FileInfo($after)), [Siemens.Engineering.ExportOptions]::WithDefaults)
            $confirmed = New-Object Xml.XmlDocument
            $confirmed.Load($after)
            $confirmedMembers = @($confirmed.SelectNodes($query))
            if ($confirmedMembers.Count -ne $members.Count -or @($confirmedMembers | Where-Object { $_.GetAttribute('Remanence') -ne 'Retain' }).Count -gt 0) {
                throw 'Native export did not confirm retention for every requested member.'
            }
            $check.verified = $true
        } catch {
            $complete = $false
            $check.message = $_.Exception.Message
        }
        $report.retentionChecks += $check
    }
    return $complete
}

try {
    if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit Windows PowerShell; TIA V19 Openness is x64.' }
    if (-not (Test-Path -LiteralPath $ApiPath)) { throw "Missing TIA V19 Openness API: $ApiPath. Install the TIA Openness component from the Siemens V19 installer." }
    foreach ($entry in (Get-Content -LiteralPath (Join-Path $Root 'reports\source-hashes.json') -Raw | ConvertFrom-Json).PSObject.Properties) {
        $path = Join-Path $Root $entry.Name
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $entry.Value) { throw "Source hash mismatch: $($entry.Name). Regenerate the sources before building." }
    }
    $config = Get-Content -LiteralPath (Join-Path $Root 'openness\target.json') -Raw | ConvertFrom-Json
    [Reflection.Assembly]::LoadFrom($ApiPath) | Out-Null
    # Optional assemblies are loaded from the same V19 PublicAPI folder.
    foreach ($name in @('Siemens.Engineering.Hmi.dll', 'Siemens.Engineering.HW.dll')) {
        $extra = Join-Path (Split-Path -Parent $ApiPath) $name
        if (Test-Path -LiteralPath $extra) { [Reflection.Assembly]::LoadFrom($extra) | Out-Null }
    }
    $report.phase = 'create_project'
    Write-Host 'Starting TIA V19. Accept the TIA Openness access prompt for this local builder if shown.'
    $tia = New-Object Siemens.Engineering.TiaPortal -ArgumentList ([Siemens.Engineering.TiaPortalMode]::WithUserInterface)
    $project = $tia.Projects.Create((New-Object IO.DirectoryInfo($runDirectory)), $projectName)
    $report.phase = 'cpu_catalog'
    $created = Create-Device $project $config.cpuIdentifiers 'ROLL_CPU1513'
    $report.cpuCatalogIdentifier = $created.Identifier
    $plc = Find-Software $created.Device
    Export-ApiDescription $plc 'plc-api.json'
    $report.phase = 'source_import'
    # Only delete the default OB1 in this newly created project, before importing
    # our OB1. Never opens or edits an existing user project.
    foreach ($block in @($plc.BlockGroup.Blocks)) {
        if ($block.GetType().Name -eq 'OB') {
            $number = Read-BlockNumber $block
            if (($number -eq 1) -or ($block.Name -eq 'Main')) { $block.Delete() }
        }
    }
    $sourceFile = New-Object IO.FileInfo((Join-Path $Root 'ROLL_ALL.scl'))
    $source = $plc.ExternalSourceGroup.ExternalSources.CreateFromFile('ROLL_ALL', $sourceFile)
    $source.GenerateBlocksFromSource() | Out-Null
    $expected = [regex]::Matches([IO.File]::ReadAllText($sourceFile.FullName), '(?m)^(?:FUNCTION|DATA_BLOCK) "([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    $present = @($plc.BlockGroup.Blocks | ForEach-Object { $_.Name })
    $report.sourceInventoryMissing = @($expected | Where-Object { $_ -notin $present })
    $obNumbers = @()
    foreach ($block in $plc.BlockGroup.Blocks) {
        if ($block.GetType().Name -eq 'OB') {
            $obNumbers += Read-BlockNumber $block
        }
    }
    if (1 -notin $obNumbers) { $report.sourceInventoryMissing += 'OB1 (ProgramCycle)' }
    if (100 -notin $obNumbers) { $report.sourceInventoryMissing += 'OB100 (Startup)' }
    $report.sourceInventoryComplete = $report.sourceInventoryMissing.Count -eq 0
    $report.phase = 'plc_compile'
    $compiler = Get-Service $plc 'Siemens.Engineering.Compiler.ICompilable'
    if ($null -eq $compiler) { throw 'STEP 7 Professional compiler service is unavailable.' }
    $compiled = $compiler.Compile()
    $report.initialPlcCompilation = [ordered]@{ state = [string]$compiled.State; errorCount = $compiled.ErrorCount; warningCount = $compiled.WarningCount; messages = @(Compiler-Messages $compiled) }
    if ($report.sourceInventoryComplete -and $compiled.ErrorCount -eq 0) {
        $report.phase = 'retention_configuration'
        $retentionDirectory = Join-Path $runDirectory 'native-retention'
        [IO.Directory]::CreateDirectory($retentionDirectory) | Out-Null
        $report.retentionConfigured = Configure-Retention $plc $retentionDirectory
        $report.phase = 'plc_compile_after_retention'
        $compiled = $compiler.Compile()
    }
    $report.plcCompilation = [ordered]@{
        state = [string]$compiled.State; errorCount = $compiled.ErrorCount
        warningCount = $compiled.WarningCount; messages = @(Compiler-Messages $compiled)
    }
    $nativeDirectory = Join-Path $runDirectory 'native-blocks'
    [IO.Directory]::CreateDirectory($nativeDirectory) | Out-Null
    foreach ($block in $plc.BlockGroup.Blocks) {
        try {
            $block.Export((New-Object IO.FileInfo((Join-Path $nativeDirectory ($block.Name + '.xml')))), [Siemens.Engineering.ExportOptions]::WithDefaults)
        } catch { $report.warnings += "Export $($block.Name): $($_.Exception.Message)" }
    }
    # Persist PLC work even if WinCC/catalog creation fails.
    $project.Save()
    $report.phase = 'hmi_catalog'
    $createdHmi = Create-Device $project $config.hmiIdentifiers 'ROLL_TP900'
    $report.hmiCatalogIdentifier = $createdHmi.Identifier
    $hmi = Find-Software $createdHmi.Device
    Export-ApiDescription $hmi 'hmi-api.json'
    foreach ($property in @('ScreenFolder', 'TagFolder', 'Connections', 'AlarmClasses', 'DiscreteAlarms')) {
        if ($null -ne $hmi.PSObject.Properties[$property]) { Export-ApiDescription $hmi.$property ('hmi-' + $property + '-api.json') }
    }
    if ($null -ne $hmi.PSObject.Properties['TagFolder'] -and $null -ne $hmi.TagFolder.PSObject.Properties['TagTables']) {
        Export-ApiDescription $hmi.TagFolder.TagTables 'hmi-tag-tables-composition-api.json'
        try {
            $tagTable = $hmi.TagFolder.TagTables.Create('ROLL')
            Export-ApiDescription $tagTable 'hmi-tag-table-api.json'
            Export-ApiDescription $tagTable.Tags 'hmi-tags-composition-api.json'
            # Native internal probe tag supplies the real V19 export structure.
            $probeTag = $tagTable.Tags.Create('BuilderProbe')
            Export-ApiDescription $probeTag 'hmi-tag-api.json'
            try {
                $probeFile = New-Object IO.FileInfo((Join-Path $runDirectory 'hmi-probe-tags.xml'))
                $tagTable.Export($probeFile, [Siemens.Engineering.ExportOptions]::WithDefaults)
            }
            catch { $report.warnings += 'Probe tag export: ' + $_.Exception.Message }
        } catch { $report.warnings += 'Probe tag creation: ' + $_.Exception.Message }
    }
    # Create native screen objects through the installed API. Controls, tags,
    # connection and alarms require actual WinCC V19 export schema from this run.
    # Never import invented XML or present blank screens as an operational HMI.
    if ($null -ne $hmi.PSObject.Properties['ScreenFolder'] -and $null -ne $hmi.ScreenFolder.PSObject.Properties['Screens']) {
        Export-ApiDescription $hmi.ScreenFolder.Screens 'hmi-screens-composition-api.json'
        foreach ($screenName in $config.screenNames) {
            try {
                $screen = $hmi.ScreenFolder.Screens.Create([string]$screenName)
                $report.nativeScreens += [string]$screenName
                Export-ApiDescription $screen ('screen-' + $screenName + '-api.json')
                if ($null -ne $screen.PSObject.Properties['ScreenItems']) { Export-ApiDescription $screen.ScreenItems ('screen-' + $screenName + '-items-api.json') }
                try {
                    $screen.Export((New-Object IO.FileInfo((Join-Path $runDirectory ('screen-' + $screenName + '.xml')))), [Siemens.Engineering.ExportOptions]::WithDefaults)
                } catch { $report.warnings += "Screen export $screenName : $($_.Exception.Message)" }
            } catch { $report.warnings += "Screen creation $screenName : $($_.Exception.Message)" }
        }
    } else {
        $report.warnings += 'Installed HMI API exposes a different screen interface; see hmi-api.json.'
    }
    $project.Save()
    if ($report.sourceInventoryComplete -and $compiled.ErrorCount -eq 0 -and [string]$compiled.State -eq 'Success') {
        $report.status = 'plc_compiled_hmi_io_pending'
        if (-not $report.retentionConfigured) { $report.status = 'plc_compiled_retention_hmi_io_pending' }
        $exitCode = 0
    } elseif ($report.sourceInventoryComplete -and $compiled.ErrorCount -eq 0 -and $compiled.WarningCount -gt 0) {
        $report.status = 'plc_compiled_with_warnings_hmi_io_pending'
        if (-not $report.retentionConfigured) { $report.status = 'plc_compiled_with_warnings_retention_hmi_io_pending' }
        $exitCode = 0
    } else {
        $report.status = 'plc_compile_failed'
    }
    $report.phase = 'saved'
} catch {
    $report.status = 'blocked'
    $report.errors += $_.Exception.ToString()
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    if ($null -ne $project) {
        try { $project.Save() } catch { $report.errors += 'Project save: ' + $_.Exception.Message }
        try { $report.projectFile = $project.Path.FullName } catch { }
    }
    $report.finished = (Get-Date).ToString('o')
    $report.reportArchive = Join-Path $OutputDirectory ($projectName + '_raport.zip')
    Save-Report
    if ($null -ne $tia) {
        try { $tia.Dispose() } catch { $report.warnings += 'TIA cleanup: ' + $_.Exception.Message; Save-Report }
    }
    try {
        $reportFiles = @(Get-ChildItem -LiteralPath $runDirectory -File | Where-Object { $_.Extension -in @('.json', '.xml') } | ForEach-Object { $_.FullName })
        $nativeFolder = Join-Path $runDirectory 'native-blocks'
        if (Test-Path -LiteralPath $nativeFolder) { $reportFiles += $nativeFolder }
        $retentionFolder = Join-Path $runDirectory 'native-retention'
        if (Test-Path -LiteralPath $retentionFolder) { $reportFiles += $retentionFolder }
        Compress-Archive -LiteralPath $reportFiles -DestinationPath $report.reportArchive
    } catch {
        $report.warnings += 'Report archive: ' + $_.Exception.Message
        $report.reportArchive = $null
        Save-Report
    }
    Write-Host "Report folder: $runDirectory"
    if ($null -ne $report.reportArchive) { Write-Host "Report ZIP: $($report.reportArchive)" }
    Write-Host 'Send build-report.json and the native screen/API exports back for completing the TP900 project.'
    Write-Host 'This run does not configure physical I/O, complete HMI controls or download anything.'
}
exit $exitCode
