# SPDX-License-Identifier: LGPL-3.0-or-later
#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$DocumentPath,
    [string]$CompanionDirectory,
    [switch]$Export,
    [switch]$OpenIfNeeded
)

$ErrorActionPreference = 'Stop'

function Resolve-CadLinkCompanion([string]$ExplicitPath, [string]$StartDirectory) {
    $configured = $ExplicitPath
    if (-not $configured) { $configured = $env:CAD_LINK_INVENTOR_HOME }
    if ($configured) {
        $resolved = [IO.Path]::GetFullPath($configured)
        if (-not [IO.File]::Exists((Join-Path $resolved 'CadLink-ExportGLB.iLogicVb'))) {
            throw 'The configured companion directory does not contain CadLink-ExportGLB.iLogicVb.'
        }
        return $resolved
    }
    $current = [IO.DirectoryInfo]::new($StartDirectory)
    while ($null -ne $current) {
        foreach ($candidate in @($current.FullName, (Join-Path $current.FullName 'tools\cad-link\inventor'))) {
            if ([IO.File]::Exists((Join-Path $candidate 'CadLink-ExportGLB.iLogicVb'))) { return $candidate }
        }
        $current = $current.Parent
    }
    return $null
}

function Read-CadLinkExportConfig([string]$Filename) {
    if (-not [IO.File]::Exists($Filename)) { return $null }
    $settings = [Xml.XmlReaderSettings]::new()
    $settings.DtdProcessing = [Xml.DtdProcessing]::Prohibit
    $settings.XmlResolver = $null
    $settings.MaxCharactersInDocument = 8192
    $reader = [Xml.XmlReader]::Create($Filename, $settings)
    try {
        $xml = [Xml.XmlDocument]::new()
        $xml.XmlResolver = $null
        $xml.Load($reader)
    } finally { $reader.Dispose() }
    if ($xml.DocumentElement.Name -ne 'CadLinkInventorExport') { throw 'Invalid export configuration root.' }
    $result = @{}
    foreach ($name in @('Enabled', 'ItemsRoot', 'TranslatorClassId', 'MaxFileBytes')) {
        $node = $xml.DocumentElement.SelectSingleNode($name)
        if ($null -eq $node) { throw ('Missing export configuration field: ' + $name) }
        $result[$name] = $node.InnerText.Trim()
    }
    return $result
}

function Get-CadLinkCanonicalSource([string]$ItemsRoot, [string]$Filename) {
    if (-not $ItemsRoot -or -not [IO.Path]::IsPathRooted($ItemsRoot)) { throw 'An absolute ItemsRoot is required.' }
    if (-not $Filename -or -not [IO.Path]::IsPathRooted($Filename)) { throw 'An exact absolute DocumentPath is required.' }
    if ($ItemsRoot.StartsWith('\\?\') -or $ItemsRoot.StartsWith('\\.\') -or $Filename.StartsWith('\\?\') -or $Filename.StartsWith('\\.\')) { throw 'Device paths are not supported.' }
    $root = [IO.Path]::GetFullPath($ItemsRoot).TrimEnd('\')
    $source = [IO.Path]::GetFullPath($Filename)
    $extension = [IO.Path]::GetExtension($source).ToLowerInvariant()
    if ($extension -notin @('.ipt', '.iam')) { throw 'Only IPT and IAM source documents are supported.' }
    $folder = [IO.Path]::GetDirectoryName($source)
    if (-not [string]::Equals([IO.Path]::GetDirectoryName($folder), $root, [StringComparison]::OrdinalIgnoreCase) -or
        -not [string]::Equals([IO.Path]::GetFileName($folder), [IO.Path]::GetFileNameWithoutExtension($source), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Source must match ItemsRoot\code\code.ipt or .iam.'
    }
    if (-not [IO.File]::Exists($source)) { throw 'The exact native source does not exist.' }
    $otherExtension = '.ipt'
    if ($extension -eq '.ipt') { $otherExtension = '.iam' }
    if ([IO.File]::Exists([IO.Path]::ChangeExtension($source, $otherExtension))) { throw 'Both IPT and IAM use this basename; GLB publication would be ambiguous.' }
    $cursor = $source
    while ($cursor) {
        if (([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse points are not supported.' }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $source
}

function Assert-CadLinkDocumentReady($Document) {
    $documents = @($Document)
    foreach ($dependency in $Document.AllReferencedDocuments) { $documents += $dependency }
    foreach ($entry in $documents) {
        if ($entry.Dirty -or $entry.RequiresUpdate) { throw ('Document or dependency needs to be updated and saved: ' + $entry.FullFileName) }
        if (-not $entry.FullFileName -or -not [IO.File]::Exists($entry.FullFileName)) { throw 'An unsaved or unresolved document prevents export.' }
        foreach ($descriptor in $entry.ReferencedDocumentDescriptors) {
            if ($descriptor.ReferenceMissing -and -not $descriptor.ReferenceSuppressed) { throw 'An unresolved component prevents export.' }
        }
    }
}

function Get-CadLinkFileState([string]$Filename) {
    if (-not [IO.File]::Exists($Filename)) { return $null }
    $info = [IO.FileInfo]::new($Filename)
    return [PSCustomObject]@{
        bytes = $info.Length
        modified_utc = $info.LastWriteTimeUtc.ToString('o')
        modified_ticks = $info.LastWriteTimeUtc.Ticks
        sha256 = (Get-FileHash -LiteralPath $Filename -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Assert-CadLinkGlb([string]$Filename, [long]$Maximum) {
    $stream = [IO.File]::Open($Filename, 'Open', 'Read', 'Read')
    try {
        if ($stream.Length -lt 24 -or $stream.Length -gt $Maximum) { throw 'Invalid GLB size.' }
        $reader = [IO.BinaryReader]::new($stream)
        if ($reader.ReadUInt32() -ne 0x46546c67 -or $reader.ReadUInt32() -ne 2 -or $reader.ReadUInt32() -ne $stream.Length) { throw 'Invalid or incomplete GLB 2.0 header.' }
        $jsonLength = $reader.ReadUInt32()
        if ($reader.ReadUInt32() -ne 0x4e4f534a -or $jsonLength -lt 4 -or ($jsonLength % 4) -ne 0 -or $jsonLength -gt ($stream.Length - 20)) { throw 'Invalid GLB JSON chunk.' }
    } finally { $stream.Dispose() }
}

function Get-CadLinkTranslatorInventory($Application) {
    $result = @()
    foreach ($addin in $Application.ApplicationAddIns) {
        try {
            $extensions = [string]$addin.FileExtensions
            $isGltf = @($extensions.Split(';') | Where-Object { $_.Trim().TrimStart('*', '.') -in @('glb', 'gltf') }).Count -gt 0
            if ($isGltf -and $addin.SupportsSaveCopyAs) {
                $result += [PSCustomObject]@{ name = [string]$addin.DisplayName; class_id = [string]$addin.ClassIdString; extensions = $extensions; active = [bool]$addin.Activated }
            }
        } catch { } # Non-translator add-ins do not have these properties.
    }
    return $result
}

function Invoke-CadLinkGlbCore($Application, [string]$Target, [string]$Companion, [bool]$DoExport, [bool]$AllowOpen, [string]$ConfigPath) {
    $config = Read-CadLinkExportConfig $ConfigPath
    $openDocuments = @()
    $matching = @()
    foreach ($entry in $Application.Documents) {
        $openDocuments += [PSCustomObject]@{ path = [string]$entry.FullFileName; dirty = [bool]$entry.Dirty; requires_update = [bool]$entry.RequiresUpdate }
        if ($Target -and [string]::Equals([string]$entry.FullFileName, [IO.Path]::GetFullPath($Target), [StringComparison]::OrdinalIgnoreCase)) { $matching += $entry }
    }
    if ($matching.Count -gt 1) { throw 'Multiple open documents/model states match this path; select a single document before exporting.' }
    if (-not $DoExport) {
        if ($AllowOpen) { throw '-OpenIfNeeded requires -Export; inspection never opens documents.' }
        return [PSCustomObject]@{
            mode = 'inspect'; inventor = [string]$Application.SoftwareVersion.DisplayName; ready = [bool]$Application.Ready
            companion_directory = $Companion; configuration = $ConfigPath; configured = ($null -ne $config)
            export_enabled = ($null -ne $config -and $config.Enabled -ceq 'true')
            items_root = $(if ($null -ne $config) { $config.ItemsRoot } else { $null })
            target_open = ($matching.Count -eq 1); open_documents = $openDocuments
            gltf_translators = @(Get-CadLinkTranslatorInventory $Application)
        }
    }
    if (-not $Application.Ready) { throw 'Inventor is not ready. Finish the current command and inspect again.' }
    if (-not $Companion) { throw 'Locate the companion with -CompanionDirectory or CAD_LINK_INVENTOR_HOME.' }
    if ($null -eq $config -or $config.Enabled -cne 'true') { throw 'Export must already be enabled in the local export.xml configuration.' }
    $source = Get-CadLinkCanonicalSource $config.ItemsRoot $Target
    $maximum = [long]::Parse($config.MaxFileBytes, [Globalization.CultureInfo]::InvariantCulture)
    if ($maximum -lt 1024 -or $maximum -gt 268435456) { throw 'Invalid configured GLB size limit.' }
    $output = [IO.Path]::ChangeExtension($source, '.glb')
    $beforeSource = Get-CadLinkFileState $source
    $beforeGlb = Get-CadLinkFileState $output
    $owned = $false
    $document = $null
    $result = $null
    try {
        if ($matching.Count -eq 1) { $document = $matching[0] }
        elseif ($AllowOpen) { $document = $Application.Documents.Open($source, $false); $owned = $true }
        else { throw 'The exact document is not open. Open it in Inventor, or explicitly use -OpenIfNeeded.' }
        Assert-CadLinkDocumentReady $document
        # Autodesk publishes this iLogic add-in ID in its developer API examples.
        $addin = $Application.ApplicationAddIns.ItemById('{3BDD8D79-2179-4B11-8A5A-257B1C0263AC}')
        if (-not $addin.Activated) { $addin.Activate() }
        $automation = $addin.Automation
        $rule = Join-Path $Companion 'CadLink-ExportGLB.iLogicVb'
        $started = [DateTime]::UtcNow
        $returnCode = $automation.RunExternalRule($document, $rule)
        $afterSource = Get-CadLinkFileState $source
        if ($beforeSource.sha256 -ne $afterSource.sha256 -or $beforeSource.modified_ticks -ne $afterSource.modified_ticks) { throw 'The native source changed during execution; review it. This helper does not restore or save native files.' }
        Assert-CadLinkDocumentReady $document
        if ($returnCode -ne 0) { throw ('iLogic returned a nonzero result: ' + $returnCode) }
        $afterGlb = Get-CadLinkFileState $output
        $fresh = $null -ne $afterGlb -and ([DateTime]::Parse($afterGlb.modified_utc).ToUniversalTime() -ge $started.AddSeconds(-2))
        if ($null -ne $beforeGlb) { $fresh = $fresh -and ($beforeGlb.modified_ticks -ne $afterGlb.modified_ticks -or $beforeGlb.sha256 -ne $afterGlb.sha256) }
        if (-not $fresh) { throw 'The rule returned without a newly published GLB. Inspect the local export.log; an iLogic zero result alone is not export success.' }
        Assert-CadLinkGlb $output $maximum
        $result = [PSCustomObject]@{ mode = 'export'; source = $source; output = $output; inventor = [string]$Application.SoftwareVersion.DisplayName; source_unchanged = $true; glb = $afterGlb; opened_by_helper = $owned; closed_by_helper = $false; status = [string]$Application.StatusBarText }
    } finally {
        if ($owned -and $null -ne $document) {
            try {
                Assert-CadLinkDocumentReady $document
                $now = Get-CadLinkFileState $source
                if ($now.sha256 -ne $beforeSource.sha256 -or $now.modified_ticks -ne $beforeSource.modified_ticks) { throw 'Source changed.' }
                $document.Close($true)
                if ($null -ne $result) { $result.closed_by_helper = $true }
            } catch {
                Write-Warning 'The helper opened this document but left it open because it is dirty, needs updating, changed on disk, or could not close safely.'
            }
        }
    }
    return $result
}

# Dot-sourcing exposes pure helpers for synthetic tests; it never attaches COM.
if ($MyInvocation.InvocationName -ne '.') {
    if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') { throw 'Run Windows PowerShell 5.1 with -STA in the interactive Inventor user session.' }
    if ([IntPtr]::Size -ne 8) { throw 'Use 64-bit Windows PowerShell.' }
    $sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
    $instances = @([Diagnostics.Process]::GetProcessesByName('Inventor') | Where-Object { $_.SessionId -eq $sessionId })
    if ($instances.Count -ne 1) { throw 'Exactly one running Inventor instance is required in this Windows session.' }
    $companion = Resolve-CadLinkCompanion $CompanionDirectory $PSScriptRoot
    $configuration = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'CAD-link\Inventor\export.xml'
    try { $application = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application') }
    catch { throw 'Cannot attach to the existing Inventor session. Use the same Windows user and elevation as Inventor; do not start a service or another Inventor process.' }
    $expectedWindow = $instances[0].MainWindowHandle.ToInt64()
    if ($expectedWindow -eq 0 -or [long]$application.MainFrameHWND -ne $expectedWindow) { throw 'The COM application does not match the Inventor window in this session.' }
    Invoke-CadLinkGlbCore $application $DocumentPath $companion $Export.IsPresent $OpenIfNeeded.IsPresent $configuration | ConvertTo-Json -Depth 8
}
