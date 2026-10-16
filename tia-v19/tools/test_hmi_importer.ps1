param([string]$Importer = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Import-RollHmi.ps1'))
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Importer, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw ($errors | Out-String) }
foreach ($name in @('New-RollProjectArchive', 'Assert-RollHmiManifest')) {
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
        public void Archive(DirectoryInfo directory, string name, ArchiveMode mode) {
            if(mode != ArchiveMode.Compressed) throw new Exception("Wrong archive mode");
            Called=true; File.WriteAllText(Path.Combine(directory.FullName,name+".zap19"),"API double only");
        }
    }
    public class LegacyArchive {
        public bool Called;
        public void Archive(DirectoryInfo directory, string name, bool discardRestorableData) {
            if(discardRestorableData) throw new Exception("Restorable data must be retained");
            Called=true; File.WriteAllText(Path.Combine(directory.FullName,name+".zap19"),"API double only");
        }
    }
    public class UnsupportedArchive {
        public bool Called;
        public void Archive(DirectoryInfo directory, string name, bool unknownFlag) { Called=true; }
    }
}
'@
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('roll-hmi-import-tests-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temporary) | Out-Null
try {
    foreach ($type in @('EnumArchive','LegacyArchive')) {
        $project = New-Object ('RollHmiTest.' + $type)
        $file = New-RollProjectArchive $project (Join-Path $temporary $type) 'source'
        if (-not $project.Called -or -not $file.Exists) { throw 'Archive API adaptation failed.' }
    }
    $unsupported = New-Object RollHmiTest.UnsupportedArchive
    $rejected = $false
    try { New-RollProjectArchive $unsupported (Join-Path $temporary 'unsupported') 'source' | Out-Null } catch { $rejected = $true }
    if (-not $rejected -or $unsupported.Called) { throw 'Unknown archive flags must not be guessed.' }
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
    $calls = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.InvokeMemberExpressionAst] }, $true))
    if (@($calls | Where-Object { $_.Member.Value -in @('Download','GenerateBlocksFromSource','SetAttribute','SetAttributes','CreateWithItem') }).Count -ne 0) { throw 'Importer contains an unexpected PLC/hardware mutation.' }
    $close = $ast.Extent.Text.IndexOf('$source.Close()')
    $archive = $ast.Extent.Text.IndexOf('$archive = New-RollProjectArchive')
    if ($archive -lt 0 -or $close -le $archive) { throw 'Source must be archived before close.' }
    $result = [ordered]@{
        success = $true; parserVersion = $PSVersionTable.PSVersion.ToString()
        archiveApiDoubleScenarios = 3; manifestScenarios = 2; sourceArchiveOrderPassed = $true
        nativeTiaExecuted = $false; nativeProjectArchiveVerified = $false; nativeHmiImportVerified = $false
        importerSHA256 = (Get-FileHash -LiteralPath $Importer -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'reports/hmi-importer-tests.json') -Encoding UTF8
    Write-Host 'Passed: importer parser, 3 archive API scenarios, 2 manifest scenarios and archive-before-close ordering. Native TIA was not executed.'
} finally { Remove-Item -LiteralPath $temporary -Recurse -Force }
