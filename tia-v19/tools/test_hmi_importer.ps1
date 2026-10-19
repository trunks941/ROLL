param([string]$Importer = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Import-RollHmi.ps1'))
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Importer, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw ($errors | Out-String) }
foreach ($name in @('New-RollProjectArchive', 'Assert-RollCircleGeometry', 'Assert-RollHmiManifest')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    if ($null -eq $definition) { throw "Missing function: $name" }
    . ([scriptblock]::Create($definition.Extent.Text))
}
Add-Type -TypeDefinition @'
using System;
using System.IO;
namespace RollHmiTest {
    public enum ArchiveMode { Compressed, Uncompressed }
    public class EnumArchive {
        public bool Called;
        public string ReceivedName;
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) {
            if(mode != ArchiveMode.Compressed) throw new Exception("Wrong archive mode");
            Called=true; ReceivedName=name;
            File.WriteAllText(Path.Combine(directory.FullName,name),"API double only");
        }
    }
    public class LegacyArchive {
        public bool Called;
        public void Archive(DirectoryInfo directory, string name, bool discardRestorableData) {
            if(discardRestorableData) throw new Exception("Restorable data must be retained");
            Called=true; File.WriteAllText(Path.Combine(directory.FullName,name),"API double only");
        }
    }
    public class UnsupportedArchive {
        public bool Called;
        public void Archive(DirectoryInfo directory, string name, bool unknownFlag) { Called=true; }
    }
    public class EmptyArchive {
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) {
            File.WriteAllText(Path.Combine(directory.FullName,name),"");
        }
    }
    public class MissingArchive {
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) { }
    }
    public class WrongNameArchive {
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) {
            File.WriteAllText(Path.Combine(directory.FullName,"extensionless-target"),"API double only");
        }
    }
    public class ThrowingArchive {
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) {
            File.WriteAllText(Path.Combine(directory.FullName,"partial.tmp"),"API double only");
            throw new InvalidOperationException("Archive API failure");
        }
    }
}
'@
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('roll-hmi-import-tests-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temporary) | Out-Null
try {
    foreach ($type in @('EnumArchive','LegacyArchive')) {
        $project = New-Object ('RollHmiTest.' + $type)
        $diagnostics = [ordered]@{}
        $file = New-RollProjectArchive $project (Join-Path $temporary $type) 'source.zap19' $diagnostics
        if (-not $project.Called -or -not $file.Exists -or $file.Name -ne 'source.zap19' -or
            -not $diagnostics.returnedWithoutException -or -not $diagnostics.expectedFileVerified -or
            $diagnostics.requestedFileName -ne 'source.zap19' -or $diagnostics.files.Count -ne 1) { throw 'Archive API adaptation or diagnostics failed.' }
    }
    $unsupported = New-Object RollHmiTest.UnsupportedArchive
    $rejected = $false
    try { New-RollProjectArchive $unsupported (Join-Path $temporary 'unsupported') 'source.zap19' | Out-Null } catch { $rejected = $true }
    if (-not $rejected -or $unsupported.Called) { throw 'Unknown archive flags must not be guessed.' }
    $invalidNames = @('source', 'source.zip', '../source.zap19', '..\source.zap19')
    foreach ($name in $invalidNames) {
        $project = New-Object RollHmiTest.EnumArchive
        $rejected = $false
        try { New-RollProjectArchive $project (Join-Path $temporary 'invalid-name') $name | Out-Null } catch { $rejected = $true }
        if (-not $rejected -or $project.Called) { throw "Incomplete or invalid archive name accepted: $name" }
    }
    $project = New-Object RollHmiTest.EnumArchive
    $rejected = $false
    try { New-RollProjectArchive $project (Join-Path $temporary 'EnumArchive') 'source.zap19' | Out-Null } catch { $rejected = $true }
    if (-not $rejected -or $project.Called) { throw 'Existing backup must not be overwritten.' }
    foreach ($type in @('EmptyArchive','MissingArchive','WrongNameArchive','ThrowingArchive')) {
        $project = New-Object ('RollHmiTest.' + $type)
        $diagnostics = [ordered]@{}
        $rejected = $false
        try { New-RollProjectArchive $project (Join-Path $temporary $type) 'source.zap19' $diagnostics | Out-Null } catch { $rejected = $true }
        if (-not $rejected -or $diagnostics.expectedFileVerified -or -not $diagnostics.method) { throw "Unverified archive accepted: $type" }
        if ($type -eq 'ThrowingArchive') {
            if ($diagnostics.returnedWithoutException -or $diagnostics.files[0].name -ne 'partial.tmp') { throw 'Archive API failure lost its file diagnostics.' }
        } elseif (-not $diagnostics.returnedWithoutException) { throw 'Archive return status missing.' }
        if ($type -eq 'WrongNameArchive' -and $diagnostics.files[0].name -ne 'extensionless-target') { throw 'Unexpected archive file name missing from diagnostics.' }
    }
    $root = Split-Path -Parent $PSScriptRoot
    $native = Join-Path $root 'hmi/native'
    $manifest = Assert-RollHmiManifest $native
    if ($manifest.tag_count -ne 53 -or $manifest.files.Count -ne 11) { throw 'Native manifest contract mismatch.' }
    $copy = Join-Path $temporary 'manifest-copy'
    Copy-Item -LiteralPath $native -Destination $copy -Recurse
    $bad = Get-Content -LiteralPath (Join-Path $copy 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $bad.files[0].sha256 = '0' * 64
    $bad | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $copy 'manifest.json') -Encoding UTF8
    $rejected = $false
    try { Assert-RollHmiManifest $copy | Out-Null } catch { $rejected = $true }
    if (-not $rejected) { throw 'Changed native assets must be rejected before attaching to TIA.' }
    # Correct hashes must not conceal an invalid native property dependency.
    # The first case reproduces V19's actual 20px / Radius=24 rejection.
    $screenEntry = @($manifest.files | Where-Object { $_.path -eq 'screens/ROLL_Alarmy.xml' })[0]
    foreach ($case in @(@{ Property = 'Radius'; Value = '24' }, @{ Property = 'Height'; Value = '22' }, @{ Property = 'Width'; Value = '0' })) {
        $screenPath = Join-Path $copy $screenEntry.path
        Copy-Item -LiteralPath (Join-Path $native $screenEntry.path) -Destination $screenPath -Force
        $document = New-Object Xml.XmlDocument
        $document.Load($screenPath)
        $document.SelectSingleNode('//Hmi.Screen.Circle/AttributeList/' + $case.Property).InnerText = $case.Value
        $document.Save($screenPath)
        $bad = Get-Content -LiteralPath (Join-Path $native 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        @($bad.files | Where-Object { $_.path -eq $screenEntry.path })[0].sha256 = (Get-FileHash -LiteralPath $screenPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $bad | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $copy 'manifest.json') -Encoding UTF8
        $rejected = $false
        try { Assert-RollHmiManifest $copy | Out-Null } catch { $rejected = $_.Exception.Message -like 'Invalid circle geometry*' }
        if (-not $rejected) { throw "Invalid $($case.Property) must be rejected before attaching to TIA, even with a correct file hash." }
    }
    $calls = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.InvokeMemberExpressionAst] }, $true))
    if (@($calls | Where-Object { $_.Member.Value -in @('Download','GenerateBlocksFromSource','SetAttribute','SetAttributes','CreateWithItem') }).Count -ne 0) { throw 'Importer contains an unexpected PLC/hardware mutation.' }
    $close = $ast.Extent.Text.IndexOf('$source.Close()')
    $archive = $ast.Extent.Text.IndexOf('$archive = New-RollProjectArchive')
    if ($archive -lt 0 -or $close -le $archive) { throw 'Source must be archived before close.' }
    if ($ast.Extent.Text -notmatch "New-RollProjectArchive .*'ROLL_HMI_SOURCE\.zap19'") { throw 'Importer must pass the complete archive file name.' }
    $checkpoint = $ast.Extent.Text.IndexOf('$report.copySavedBeforeImport = $true')
    $imports = $ast.Extent.Text.IndexOf("foreach (`$category in @('tags', 'skeletons', 'screens'))")
    if ($checkpoint -lt 0 -or $imports -le $checkpoint) { throw 'Retrieved copy must be saved before any native import.' }
    $result = [ordered]@{
        success = $true; parserVersion = $PSVersionTable.PSVersion.ToString()
        archiveApiDoubleScenarios = 12; manifestScenarios = 5; circleRejectionScenarios = 3; sourceArchiveOrderPassed = $true
        savedCopyBeforeImportOrderPassed = $true
        completeArchiveFileNamePassed = $true; archiveFailureDiagnosticsPassed = $true
        nativeTiaExecuted = $false; nativeProjectArchiveVerified = $false; nativeHmiImportVerified = $false
        importerSHA256 = (Get-FileHash -LiteralPath $Importer -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'reports/hmi-importer-tests.json') -Encoding UTF8
    Write-Host 'Passed: importer parser, 12 archive API/name/failure scenarios, 5 manifest/geometry scenarios and archive/checkpoint ordering. Native TIA was not executed.'
} finally { Remove-Item -LiteralPath $temporary -Recurse -Force }
