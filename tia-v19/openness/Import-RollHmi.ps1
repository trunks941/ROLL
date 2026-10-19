param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'ROLL_TIA_V19'),
    [string]$ApiPath = 'C:\Program Files\Siemens\Automation\Portal V19\PublicAPI\V19\Siemens.Engineering.dll',
    [string]$ProjectName = ''
)

# Offline HMI review import. Archive the saved source, retrieve a separate copy,
# then import only HMI tags/screens. No PLC source/hardware/security mutation,
# online access or device download. Preserve the original WZOR_ROLL alarm view.
$ErrorActionPreference = 'Stop'
$runDirectory = Join-Path $OutputDirectory ('ROLL_HMI_IMPORT_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6))
[IO.Directory]::CreateDirectory($runDirectory) | Out-Null
$report = [ordered]@{
    status = 'starting'; phase = 'prerequisites'; sourceProject = $null
    sourceArchive = $null; sourceArchiveSHA256 = $null; archiveAttempt = $null; projectFile = $null
    originalProjectModified = $false; originalReopenedAfterRetrieveFailure = $false
    sourceArchivedBeforeClose = $false; copyRetrieved = $false; copySavedBeforeImport = $false; hmi = $null
    savedImportCategories = @(); currentImportFile = $null
    imported = @(); hmiCompilation = $null; errors = @(); warnings = @()
    plcSourceChanged = $false; hardwareChanged = $false; securityChanged = $false
    originalScreenPreservedInProjectCopy = $false; alarmViewPresenceProgrammaticallyVerified = $false; hmiFullyConfigured = $false
    heartbeatConfigured = $false; physicalIoConfigured = $false
    machineTested = $false; downloadsPerformed = $false; reportArchive = $null
}
$tia = $null
$exclusive = $null
$project = $null
$originalPath = $null
$exitCode = 1

function New-RollProjectArchive($Project, [string]$Directory, [string]$FileName, [System.Collections.IDictionary]$Diagnostics = $null) {
    # Archive's targetName is a complete file name. Openness does not supply
    # the extension on our behalf. Do not close the source on an unverified copy.
    if ($FileName -notmatch '^[A-Za-z0-9_][A-Za-z0-9_.-]*\.zap19$') { throw 'Archive requires a complete .zap19 file name without a directory.' }
    [IO.Directory]::CreateDirectory($Directory) | Out-Null
    $expectedPath = Join-Path $Directory $FileName
    if (Test-Path -LiteralPath $expectedPath) { throw 'Archive destination already exists. It will not be overwritten.' }
    if ($null -ne $Diagnostics) {
        $Diagnostics['requestedFileName'] = $FileName
        $Diagnostics['method'] = $null
        $Diagnostics['mode'] = $null
        $Diagnostics['returnedWithoutException'] = $false
        $Diagnostics['files'] = @()
        $Diagnostics['expectedFileVerified'] = $false
    }
    $methods = @($Project.GetType().GetMethods() | Where-Object {
        $_.Name -eq 'Archive' -and $_.GetParameters().Count -eq 3 -and
        $_.GetParameters()[0].ParameterType -eq [IO.DirectoryInfo] -and
        $_.GetParameters()[1].ParameterType -eq [string]
    })
    $selected = $null
    $mode = $null
    foreach ($method in $methods) {
        $parameter = $method.GetParameters()[2]
        if ($parameter.ParameterType.IsEnum -and 'Compressed' -in [Enum]::GetNames($parameter.ParameterType)) {
            $selected = $method
            $mode = [Enum]::Parse($parameter.ParameterType, 'Compressed')
            break
        }
    }
    if ($null -eq $selected) {
        foreach ($method in $methods) {
            $parameter = $method.GetParameters()[2]
            if ($parameter.ParameterType -eq [bool] -and $parameter.Name -match '(?i)discard.*restorable') {
                $selected = $method; $mode = $false; break
            }
            if ($parameter.ParameterType -eq [bool] -and $parameter.Name -match '(?i)compress') {
                $selected = $method; $mode = $true; break
            }
        }
    }
    if ($null -eq $selected) { throw 'Installed SDK exposes no recognized public Archive signature. Original project remains open; see project-methods.json.' }
    $arguments = New-Object object[] 3
    $directoryInfo = New-Object IO.DirectoryInfo($Directory)
    $arguments[0] = $directoryInfo.PSObject.BaseObject
    $arguments[1] = $FileName
    $arguments[2] = $mode.PSObject.BaseObject
    if ($null -ne $Diagnostics) {
        $Diagnostics['method'] = $selected.ToString()
        $Diagnostics['mode'] = [string]$mode
    }
    try {
        $selected.Invoke($Project, $arguments) | Out-Null
        if ($null -ne $Diagnostics) { $Diagnostics['returnedWithoutException'] = $true }
    } finally {
        if ($null -ne $Diagnostics) {
            $Diagnostics['files'] = @(Get-ChildItem -LiteralPath $Directory -File | ForEach-Object {
                [ordered]@{ name = $_.Name; bytes = $_.Length }
            })
        }
    }
    $files = @(Get-ChildItem -LiteralPath $Directory -File | Where-Object { $_.Extension -eq '.zap19' })
    if ($files.Count -ne 1 -or $files[0].Name -ne $FileName -or $files[0].Length -eq 0) { throw "Archive did not produce the expected nonempty $FileName. Original project will not be closed; see archiveAttempt in the report." }
    if ($null -ne $Diagnostics) { $Diagnostics['expectedFileVerified'] = $true }
    return $files[0]
}

function Assert-RollCircleGeometry([Xml.XmlDocument]$Document, [string]$Context) {
    foreach ($circle in $Document.SelectNodes('//Hmi.Screen.Circle')) {
        $width = [int]$circle.SelectSingleNode('AttributeList/Width').InnerText
        $height = [int]$circle.SelectSingleNode('AttributeList/Height').InnerText
        $radius = [int]$circle.SelectSingleNode('AttributeList/Radius').InnerText
        if ($width -le 0 -or $width -ne $height -or $width -ne 2 * $radius) {
            throw "Invalid circle geometry in ${Context}: Width=$width, Height=$height, Radius=$radius. Expected Width = Height = 2 * Radius. No TIA import was attempted."
        }
    }
}

function Assert-RollHmiManifest([string]$Directory) {
    $manifest = Get-Content -LiteralPath (Join-Path $Directory 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.format -ne 1 -or $manifest.native_compiled -ne $false -or $manifest.plc_source_changed -ne $false) { throw 'Unexpected HMI review manifest.' }
    foreach ($entry in $manifest.files) {
        if ($entry.category -notin @('tags', 'skeletons', 'screens') -or $entry.path -notmatch '^(tags|skeletons|screens)/[A-Za-z0-9_]+\.xml$' -or $entry.path -notlike ($entry.category + '/*')) { throw 'Invalid native import path/category.' }
        $path = Join-Path $Directory $entry.path
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "HMI asset hash mismatch: $($entry.path)" }
        if ($entry.category -eq 'screens') {
            $document = New-Object Xml.XmlDocument
            $document.Load($path)
            Assert-RollCircleGeometry $document $entry.path
        }
    }
    if (@($manifest.files | Where-Object { $_.category -eq 'tags' }).Count -ne 1 -or
        @($manifest.files | Where-Object { $_.category -eq 'skeletons' }).Count -ne 5 -or
        @($manifest.files | Where-Object { $_.category -eq 'screens' }).Count -ne 5) { throw 'Incomplete HMI import inventory.' }
    return $manifest
}

function Get-RollHmiTarget($Project) {
    $targets = @()
    $plcPresent = $false
    foreach ($device in $Project.Devices) {
        try {
            $software = Find-Software $device
            if ($software.GetType().FullName -eq 'Siemens.Engineering.Hmi.HmiTarget') { $targets += $software }
            if ($software.GetType().FullName -eq 'Siemens.Engineering.SW.PlcSoftware' -and $null -ne $software.BlockGroup.Blocks.Find('ROLL_HMI')) { $plcPresent = $true }
        } catch { $report.warnings += 'Device software read: ' + $_.Exception.Message }
    }
    if ($targets.Count -ne 1 -or -not $plcPresent) { throw 'Expected one Comfort HMI and the ROLL_HMI PLC DB in the selected ROLL project.' }
    return $targets[0]
}

function Assert-RollHmiSource($Hmi, $Manifest) {
    $inventory = @(Get-HmiSeedInventory $Hmi)
    $screens = @($inventory | Where-Object { $_.Kind -eq 'Screen' })
    if (@($screens | Where-Object { $_.Name -eq $Manifest.original_screen_required }).Count -ne 1) { throw 'WZOR_ROLL is missing. Open the existing project containing the alarm view, not a new blank project.' }
    foreach ($screen in $screens) {
        if ($screen.Name -in @($Manifest.screens | ForEach-Object { $_.name })) { throw "Screen already exists: $($screen.Name). This first-import package does not overwrite existing HMI work. Open the source project before the first HMI import." }
    }
    foreach ($table in @($inventory | Where-Object { $_.Kind -eq 'TagTable' })) {
        if ($table.Name -eq $Manifest.table) { throw 'Generated tag table already exists; select the project before first HMI import.' }
        foreach ($tag in $table.NativeObject.Tags) {
            if ([string]$tag.Name -like ($Manifest.tag_prefix + '*')) { throw "HMI tag prefix collision: $($tag.Name). Source was not modified." }
        }
    }
    # Numbers are stored in the native XML, not exposed as Screen.Number.
    $preflight = Join-Path $runDirectory 'source-screen-numbers'
    [IO.Directory]::CreateDirectory($preflight) | Out-Null
    $index = 0
    foreach ($screen in $screens) {
        $index++
        $file = New-Object IO.FileInfo((Join-Path $preflight ($index.ToString() + '.xml')))
        $screen.NativeObject.Export($file, [Siemens.Engineering.ExportOptions]::WithDefaults)
        $xml = New-Object Xml.XmlDocument
        $xml.Load($file.FullName)
        $number = $xml.SelectSingleNode("//*[local-name()='Hmi.Screen.Screen']/*[local-name()='AttributeList']/*[local-name()='Number']")
        if ($null -ne $number -and [int]$number.InnerText -in @($Manifest.screens | ForEach-Object { [int]$_.number })) { throw 'Screen number 101-105 is already used in source. Source was not modified.' }
    }
}

try {
    if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit Windows PowerShell.' }
    $nativeDirectory = Join-Path $Root 'hmi\native'
    $manifest = Assert-RollHmiManifest $nativeDirectory
    if (-not (Test-Path -LiteralPath $ApiPath)) { throw "Missing TIA V19 API: $ApiPath" }
    foreach ($spec in @(
        @{ File = 'openness\Build-Roll.ps1'; Names = @('Get-Service', 'Find-Software', 'Compiler-Messages', 'Export-ApiDescription', 'Get-EngineeringCompositionMethod', 'Get-EngineeringCreationInfos') },
        @{ File = 'openness\Export-HmiSeed.ps1'; Names = @('Get-HmiSeedInventory') }
    )) {
        $tokens = $null; $parseErrors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root $spec.File), [ref]$tokens, [ref]$parseErrors)
        if ($parseErrors.Count -gt 0) { throw "Cannot parse helper: $($spec.File)" }
        foreach ($name in $spec.Names) {
            $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
            if ($null -eq $definition) { throw "Missing helper: $name" }
            . ([scriptblock]::Create($definition.Extent.Text))
        }
    }
    [Reflection.Assembly]::LoadFrom($ApiPath) | Out-Null
    foreach ($name in @('Siemens.Engineering.Hmi.dll', 'Siemens.Engineering.HW.dll')) {
        $file = Join-Path (Split-Path -Parent $ApiPath) $name
        if (Test-Path -LiteralPath $file) { [Reflection.Assembly]::LoadFrom($file) | Out-Null }
    }
    $report.phase = 'attach_source'
    $processes = @([Siemens.Engineering.TiaPortal]::GetProcesses() | Where-Object { $null -ne $_.ProjectPath })
    if ($ProjectName) { $processes = @($processes | Where-Object { [IO.Path]::GetFileNameWithoutExtension([string]$_.ProjectPath) -eq $ProjectName }) }
    if ($processes.Count -eq 0) { throw 'Open the saved ROLL project containing WZOR_ROLL in TIA V19 first.' }
    if ($processes.Count -gt 1) {
        for ($i = 0; $i -lt $processes.Count; $i++) { Write-Host ("{0}: {1}" -f ($i + 1), [IO.Path]::GetFileName([string]$processes[$i].ProjectPath)) }
        $choice = 0
        if (-not [int]::TryParse((Read-Host 'Numer projektu ROLL'), [ref]$choice) -or $choice -lt 1 -or $choice -gt $processes.Count) { throw 'Invalid project selection.' }
        $processes = @($processes[$choice - 1])
    }
    $tia = $processes[0].Attach()
    $exclusive = $tia.ExclusiveAccess('ROLL: archiwizacja zrodla i import HMI do oddzielnej kopii')
    $projects = @($tia.Projects)
    if ($projects.Count -ne 1) { throw 'Expected one open project in selected TIA instance.' }
    $source = $projects[0]
    $report.sourceProject = [string]$source.Name
    $originalPath = $source.Path.FullName
    if ($source.IsModified) { throw 'Save the source project in TIA before importing. The script has not changed it.' }
    Export-ApiDescription $source 'project-api.json'
    @($source.GetType().GetMethods() | Where-Object { $_.Name -in @('Archive', 'Close', 'Save') } | ForEach-Object { $_.ToString() }) | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'project-methods.json') -Encoding UTF8
    @($tia.Projects.GetType().GetMethods() | Where-Object { $_.Name -in @('Open', 'Retrieve') } | ForEach-Object { $_.ToString() }) | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'project-composition-methods.json') -Encoding UTF8
    $sourceHmi = Get-RollHmiTarget $source
    Assert-RollHmiSource $sourceHmi $manifest
    $report.phase = 'archive_source'
    Write-Host 'Tworze archiwum zapisanego projektu. Zrodlo pozostanie zachowane.'
    $report.archiveAttempt = [ordered]@{}
    $archive = New-RollProjectArchive $source (Join-Path $runDirectory 'backup') 'ROLL_HMI_SOURCE.zap19' $report.archiveAttempt
    $report.sourceArchive = $archive.FullName
    $report.sourceArchiveSHA256 = (Get-FileHash -LiteralPath $archive.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $report.sourceArchivedBeforeClose = $true
    $report.phase = 'retrieve_copy'
    $source.Close()
    try {
        Write-Host 'Odtwarzam oddzielna kopie projektu do importu HMI.'
        $copyPath = Join-Path $runDirectory 'project-copy'
        [IO.Directory]::CreateDirectory($copyPath) | Out-Null
        $copyFolder = New-Object IO.DirectoryInfo($copyPath)
        $project = $tia.Projects.Retrieve((New-Object IO.FileInfo($archive.FullName)), $copyFolder)
        $report.copyRetrieved = $true
    } catch {
        try { $tia.Projects.Open((New-Object IO.FileInfo($originalPath))) | Out-Null; $report.originalReopenedAfterRetrieveFailure = $true } catch { $report.warnings += 'Original project reopen: ' + $_.Exception.Message }
        throw
    }
    $report.projectFile = $project.Path.FullName
    $hmi = Get-RollHmiTarget $project
    if (@(Get-HmiSeedInventory $hmi | Where-Object { $_.Kind -eq 'Screen' -and $_.Name -eq $manifest.original_screen_required }).Count -ne 1) { throw 'Retrieved project does not contain the original WZOR_ROLL screen.' }
    $report.originalScreenPreservedInProjectCopy = $true
    $report.hmi = [string]$hmi.Name
    # Native import failures can invalidate the TIA session. Persist the path
    # and a usable checkpoint before the first import, not only in finally.
    $report.phase = 'save_copy_before_import'
    $project.Save()
    $report.copySavedBeforeImport = $true
    Export-ApiDescription $hmi.VBScriptFolder 'hmi-vbscript-folder-api.json'
    Export-ApiDescription $hmi.VBScriptFolder.VBScripts 'hmi-vbscripts-composition-api.json'
    Export-ApiDescription $hmi.ScreenGlobalElements 'hmi-global-elements-api.json'
    Export-ApiDescription $hmi.ScreenTemplateFolder 'hmi-screen-template-folder-api.json'
    Export-ApiDescription $project.LanguageSettings 'project-language-settings-api.json'
    foreach ($category in @('tags', 'skeletons', 'screens')) {
        $report.phase = 'import_' + $category
        Write-Host ('Import HMI: ' + $category)
        foreach ($entry in @($manifest.files | Where-Object { $_.category -eq $category })) {
            $report.currentImportFile = $entry.path
            $file = New-Object IO.FileInfo((Join-Path $nativeDirectory $entry.path))
            if ($category -eq 'tags') { $hmi.TagFolder.TagTables.Import($file, [Siemens.Engineering.ImportOptions]::Override) | Out-Null }
            else { $hmi.ScreenFolder.Screens.Import($file, [Siemens.Engineering.ImportOptions]::Override) | Out-Null }
            $report.imported += [ordered]@{ category = $category; path = $entry.path; sha256 = $entry.sha256 }
            $report.currentImportFile = $null
        }
        $report.phase = 'save_' + $category
        $project.Save()
        $report.savedImportCategories += $category
    }
    $report.phase = 'compile_hmi'
    Write-Host 'Uruchamiam kompilacje WinCC V19 w kopii projektu.'
    $compiler = Get-Service $hmi 'Siemens.Engineering.Compiler.ICompilable'
    if ($null -eq $compiler) { throw 'WinCC compiler service unavailable.' }
    $compiled = $compiler.Compile()
    $report.hmiCompilation = [ordered]@{ state = [string]$compiled.State; errorCount = $compiled.ErrorCount; warningCount = $compiled.WarningCount; messages = @(Compiler-Messages $compiled) }
    $project.Save()
    $report.status = if ($compiled.ErrorCount -eq 0) { 'hmi_review_import_compiled_controls_locked' } else { 'hmi_review_compile_failed' }
    if ($compiled.ErrorCount -eq 0) { $exitCode = 0 }
    $report.phase = 'saved_copy'
} catch {
    $report.status = 'blocked'
    $report.errors += $_.Exception.ToString()
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    if ($null -ne $project) {
        try { $project.Save(); $report.projectFile = $project.Path.FullName } catch { $report.errors += 'Copy save: ' + $_.Exception.Message; $exitCode = 1 }
        try {
            $exportDirectory = Join-Path $runDirectory 'native-import-result'
            [IO.Directory]::CreateDirectory($exportDirectory) | Out-Null
            $hmi = Get-RollHmiTarget $project
            foreach ($screen in $hmi.ScreenFolder.Screens) {
                if ($screen.Name -like 'ROLL_*') {
                    $screen.Export((New-Object IO.FileInfo((Join-Path $exportDirectory ($screen.Name + '.xml')))), [Siemens.Engineering.ExportOptions]::WithDefaults)
                }
            }
        } catch { $report.warnings += 'Post-import native export: ' + $_.Exception.Message }
    }
    if ($null -ne $exclusive) { try { $exclusive.Dispose() } catch { $report.warnings += 'TIA exclusive access release: ' + $_.Exception.Message } }
    if ($null -ne $tia) { try { $tia.Dispose() } catch { $report.warnings += 'TIA detach: ' + $_.Exception.Message } }
    $report.finished = (Get-Date).ToString('o')
    $report.reportArchive = $runDirectory + '_raport.zip'
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runDirectory 'hmi-import-report.json') -Encoding UTF8
    try {
        $files = @(Get-ChildItem -LiteralPath $runDirectory -File | Where-Object { $_.Extension -eq '.json' } | ForEach-Object { $_.FullName })
        $nativeExports = Join-Path $runDirectory 'native-import-result'
        if (Test-Path -LiteralPath $nativeExports) { $files += $nativeExports }
        Compress-Archive -LiteralPath $files -DestinationPath $report.reportArchive
    } catch { Write-Host ('Report ZIP: ' + $_.Exception.Message); $exitCode = 1 }
    Write-Host ('Wynik: ' + $report.status)
    Write-Host ('Kopia projektu: ' + $report.projectFile)
    Write-Host ('Archiwum zrodla: ' + $report.sourceArchive)
    Write-Host ('Przeslij raport: ' + $report.reportArchive)
    Write-Host 'Pierwszy import HMI do weryfikacji. Edycja i polecenia operatorskie nowych ekranow pozostaja zablokowane.'
}
exit $exitCode
