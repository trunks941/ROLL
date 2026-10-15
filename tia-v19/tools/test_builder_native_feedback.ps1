param([string]$Builder = (Join-Path (Split-Path -Parent $PSScriptRoot) 'openness/Build-Roll.ps1'))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Builder, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Builder parsing failed.' }
foreach ($name in @('Compiler-Messages', 'Configure-Retention', 'Get-EngineeringCompositionMethod', 'Get-EngineeringCreationInfos', 'Export-ApiDescription')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    if ($null -eq $definition) { throw "Missing function: $name" }
    . ([scriptblock]::Create($definition.Extent.Text))
}
# Explicit-interface API doubles: no Siemens SDK is loaded or emulated beyond
# these method contracts. Retention XML fixtures are actual user V19 exports.
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
namespace Siemens.Engineering {
    public enum ExportOptions { WithDefaults }
    public enum ImportOptions { Override }
    public class EngineeringCreationInfo {
        public Type Type { get; set; }
        public string[] AttributeInfos { get; set; }
    }
    public interface IEngineeringComposition {
        IList<EngineeringCreationInfo> GetCreationInfos();
        object Create(Type type, IEnumerable<KeyValuePair<string, object>> attributes);
    }
}
namespace RollTest {
    public class Screen { public string Name { get; set; } }
    public class ExplicitComposition : Siemens.Engineering.IEngineeringComposition {
        public int Calls;
        IList<Siemens.Engineering.EngineeringCreationInfo> Siemens.Engineering.IEngineeringComposition.GetCreationInfos() {
            return new Siemens.Engineering.EngineeringCreationInfo[0];
        }
        object Siemens.Engineering.IEngineeringComposition.Create(Type type, IEnumerable<KeyValuePair<string, object>> attributes) {
            if (type != typeof(Screen)) throw new Exception("Wrong native Type");
            var values = new Dictionary<string, object>();
            foreach (var pair in attributes) values.Add(pair.Key, pair.Value);
            Calls++;
            return new Screen { Name = (string)values["Name"] };
        }
    }
    public class Block {
        public string Name;
        public XmlDocument Xml;
        public bool Dirty;
        public bool Tamper;
        public List<string> Events;
        public void Export(FileInfo path, Siemens.Engineering.ExportOptions options) {
            Events.Add("Export:" + Name);
            if (Dirty) throw new Exception("Inconsistent blocks cannot be exported before compilation.");
            var copy = (XmlDocument)Xml.CloneNode(true);
            if (Tamper && path.Name.EndsWith("-retention-check.xml")) {
                copy.SelectSingleNode("//*[@Remanence]").Attributes["Remanence"].Value = "NonRetain";
            }
            copy.Save(path.FullName);
        }
    }
    public class Blocks {
        public Dictionary<string, Block> Items = new Dictionary<string, Block>();
        public List<string> Events = new List<string>();
        public Block Find(string name) { return Items.ContainsKey(name) ? Items[name] : null; }
        public void Import(FileInfo path, Siemens.Engineering.ImportOptions options) {
            var name = path.Name.Replace("-retain-import.xml", "");
            Events.Add("Import:" + name);
            Items[name].Xml.Load(path.FullName);
            Items[name].Dirty = true;
        }
    }
    public class CompileResult {
        public string State;
        public int ErrorCount;
        public int WarningCount;
        public object[] Messages = new object[0];
    }
    public class Compiler {
        public Blocks Blocks;
        public bool Fail;
        public CompileResult Compile() {
            Blocks.Events.Add("Compile");
            if (!Fail) foreach (var block in Blocks.Items.Values) block.Dirty = false;
            return new CompileResult { State = Fail ? "Error" : "Success", ErrorCount = Fail ? 1 : 0 };
        }
    }
}
'@
$testDirectory = Join-Path ([IO.Path]::GetTempPath()) ('roll-feedback-tests-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testDirectory) | Out-Null
try {
    foreach ($scenario in @('success', 'compile_error', 'missing_db', 'retention_mismatch')) {
        $directory = Join-Path $testDirectory $scenario
        [IO.Directory]::CreateDirectory($directory) | Out-Null
        $blocks = New-Object RollTest.Blocks
        foreach ($name in @('ROLL_State', 'ROLL_DB15', 'ROLL_DB19', 'ROLL_DB205', 'ROLL_Recipe1', 'ROLL_Recipe2')) {
            if ($scenario -eq 'missing_db' -and $name -eq 'ROLL_DB15') { continue }
            $block = New-Object RollTest.Block
            $block.Name = $name
            $block.Xml = New-Object Xml.XmlDocument
            $block.Xml.Load((Join-Path $root ('native-feedback/20261015-114247/native-retention/' + $name + '-before-retention.xml')))
            $block.Events = $blocks.Events
            $block.Tamper = $scenario -eq 'retention_mismatch' -and $name -eq 'ROLL_DB15'
            $blocks.Items.Add($name, $block)
        }
        $plc = [pscustomobject]@{ BlockGroup = [pscustomobject]@{ Blocks = $blocks } }
        $compiler = New-Object RollTest.Compiler
        $compiler.Blocks = $blocks
        $compiler.Fail = $scenario -eq 'compile_error'
        $report = [ordered]@{ retentionChecks = @(); retentionPlcCompilation = $null }
        $result = Configure-Retention $plc $compiler $directory
        if ($result.Configured -ne ($scenario -eq 'success')) { throw "Incorrect retention result: $scenario" }
        if ($report.retentionChecks.Count -ne 6) { throw "Incomplete retention report: $scenario" }
        $events = @($blocks.Events)
        $compileIndex = [Array]::IndexOf($events, 'Compile')
        $imports = @(0..($events.Count - 1) | Where-Object { $events[$_] -like 'Import:*' })
        if ($compileIndex -le ($imports | Measure-Object -Maximum).Maximum) { throw 'Compilation must follow every import.' }
        if (@($events | Where-Object { $_ -eq 'Compile' }).Count -ne 1) { throw 'Unexpected duplicate compile.' }
        $verified = @($report.retentionChecks | Where-Object { $_.verified }).Count
        $expectedVerified = if ($scenario -eq 'success') { 6 } elseif ($scenario -eq 'compile_error') { 0 } else { 5 }
        if ($verified -ne $expectedVerified) { throw "Verification count mismatch: $scenario" }
        if ($scenario -eq 'success' -and $report.retentionPlcCompilation.errorCount -ne 0) { throw 'Compilation result missing.' }
    }
    $composition = New-Object RollTest.ExplicitComposition
    $creationInfos = @(Get-EngineeringCreationInfos $composition)
    if ($creationInfos.Count -ne 0 -or $composition.Calls -ne 0) { throw 'Empty native creation information must remain empty; Create must not be called.' }
    if ($null -ne $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'New-EngineeringItem' }, $true)) { throw 'Unsupported HMI creation helper was not removed.' }
    $runDirectory = $testDirectory
    Export-ApiDescription $composition 'composition-api.json'
    $description = Get-Content -LiteralPath (Join-Path $testDirectory 'composition-api.json') -Raw | ConvertFrom-Json
    if ($description.creationInfos.Count -ne 0 -or $description.interfaces.Count -ne 1) { throw 'Explicit interface metadata was not exported.' }
    $result = [ordered]@{
        success = $true; retentionScenarios = 4; emptyCreationInfoScenarios = 1; interfaceMetadataScenarios = 1; hmiCreateCalls = $composition.Calls
        parserVersion = $PSVersionTable.PSVersion.ToString()
        scope = 'retention import/compile/export ordering with native XML fixtures and API doubles; empty Comfort HMI creation info discovery with an explicit-interface API double'
        nativeTiaExecuted = $false; nativeHmiCreationVerified = $false
        builderSHA256 = (Get-FileHash -LiteralPath $Builder -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'reports/builder-native-feedback-tests.json') -Encoding UTF8
    Write-Host 'Passed: 4 retention scenarios, empty HMI creation info with no Create call, metadata export. Native TIA was not executed.'
} finally {
    Remove-Item -LiteralPath $testDirectory -Recurse -Force
}
