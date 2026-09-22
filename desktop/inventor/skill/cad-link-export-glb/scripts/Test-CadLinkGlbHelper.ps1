# SPDX-License-Identifier: LGPL-3.0-or-later
# Pure helper and fake Inventor tests. No real COM attachment or CAD data.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Invoke-CadLinkGlb.ps1')
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('cad-link-skill-test-' + [Guid]::NewGuid().ToString('N'))
$passed = 0
function Assert-True([bool]$Value, [string]$Message) { if (-not $Value) { throw $Message }; $script:passed++ }
function Assert-Throws([scriptblock]$Action, [string]$Message) { $threw = $false; try { & $Action | Out-Null } catch { $threw = $true }; Assert-True $threw $Message }
try {
    $items = Join-Path $scratch 'Items'
    $folder = Join-Path $items 'DEMO-001'
    [IO.Directory]::CreateDirectory($folder) | Out-Null
    $native = Join-Path $folder 'DEMO-001.ipt'
    [IO.File]::WriteAllText($native, 'synthetic native source')
    $nativeHash = (Get-FileHash -LiteralPath $native).Hash
    Assert-True ((Get-CadLinkCanonicalSource $items $native) -eq $native) 'Canonical source rejected.'
    Assert-Throws { Get-CadLinkCanonicalSource ($items + '-other') $native } 'Wrong root accepted.'
    Assert-Throws { Get-CadLinkCanonicalSource $items 'relative.ipt' } 'Relative source accepted.'
    $assembly = [IO.Path]::ChangeExtension($native, '.iam')
    [IO.File]::WriteAllText($assembly, 'synthetic assembly')
    Assert-Throws { Get-CadLinkCanonicalSource $items $native } 'Ambiguous IPT/IAM accepted.'
    [IO.File]::Delete($assembly)
    $config = Join-Path $scratch 'export.xml'
    [IO.File]::WriteAllText($config, '<!DOCTYPE x [<!ENTITY probe SYSTEM "file:///missing">]><CadLinkInventorExport>&probe;</CadLinkInventorExport>')
    Assert-Throws { Read-CadLinkExportConfig $config } 'External XML entities accepted.'
    $escapedItems = [Security.SecurityElement]::Escape($items)
    [IO.File]::WriteAllText($config, '<CadLinkInventorExport><Enabled>true</Enabled><ItemsRoot>' + $escapedItems + '</ItemsRoot><TranslatorClassId></TranslatorClassId><MaxFileBytes>52428800</MaxFileBytes></CadLinkInventorExport>')
    Assert-True ((Read-CadLinkExportConfig $config).ItemsRoot -eq $items) 'Configuration did not load.'
    $doc = [PSCustomObject]@{ FullFileName = $native; Dirty = $false; RequiresUpdate = $false; AllReferencedDocuments = @(); ReferencedDocumentDescriptors = @(); CloseCount = 0 }
    $doc | Add-Member ScriptMethod Close { param($skipSave) $this.CloseCount++ }
    Assert-CadLinkDocumentReady $doc
    $doc.Dirty = $true
    Assert-Throws { Assert-CadLinkDocumentReady $doc } 'Dirty document accepted.'
    $doc.Dirty = $false
    $doc.ReferencedDocumentDescriptors = @([PSCustomObject]@{ ReferenceMissing = $true; ReferenceSuppressed = $false })
    Assert-Throws { Assert-CadLinkDocumentReady $doc } 'Unresolved reference accepted.'
    $doc.ReferencedDocumentDescriptors = @()
    $other = [PSCustomObject]@{ FullFileName = 'unrelated.iam'; Dirty = $true; RequiresUpdate = $true }
    $script:ruleCalls = 0
    $script:fakeAutomation = [PSCustomObject]@{}
    $script:fakeAutomation | Add-Member ScriptMethod RunExternalRule { param($document, $rule) $script:ruleCalls++; return 0 }
    $script:fakeAddin = [PSCustomObject]@{ Activated = $true; Automation = $script:fakeAutomation }
    $addins = [PSCustomObject]@{}
    $addins | Add-Member ScriptMethod ItemById { param($id) return $script:fakeAddin }
    $app = [PSCustomObject]@{ Documents = @($doc, $other); ApplicationAddIns = $addins; Ready = $true; SoftwareVersion = [PSCustomObject]@{ DisplayName = 'synthetic' }; StatusBarText = 'synthetic' }
    $inspection = Invoke-CadLinkGlbCore $app $native $scratch $false $false $config
    Assert-True ($inspection.mode -eq 'inspect' -and $inspection.target_open) 'Inspection did not identify the exact open document.'
    Assert-True ($script:ruleCalls -eq 0 -and $doc.CloseCount -eq 0) 'Inspection executed a rule or closed a document.'
    Assert-Throws { Invoke-CadLinkGlbCore $app $native $scratch $false $true $config } 'Inspection allowed document opening.'
    $doc.Dirty = $true
    Assert-Throws { Invoke-CadLinkGlbCore $app $native $scratch $true $false $config } 'Export accepted a dirty target.'
    Assert-True ($script:ruleCalls -eq 0) 'Dirty target reached iLogic.'
    $doc.Dirty = $false
    Assert-Throws { Invoke-CadLinkGlbCore $app $native $scratch $true $false $config } 'Zero iLogic result without a GLB was reported as success.'
    Assert-True ($script:ruleCalls -eq 1) 'Synthetic iLogic was not exercised.'
    Assert-True ($doc.CloseCount -eq 0 -and $other.Dirty -and $other.RequiresUpdate) 'Existing or unrelated document state was changed.'
    Assert-True ((Get-FileHash -LiteralPath $native).Hash -eq $nativeHash) 'The original native sentinel changed.'
    $workspace = Join-Path $scratch 'workspace'
    $companion = Join-Path $workspace 'tools\cad-link\inventor'
    $installed = Join-Path $workspace '.agents\skills\cad-link-export-glb\scripts'
    [IO.Directory]::CreateDirectory($companion) | Out-Null
    [IO.Directory]::CreateDirectory($installed) | Out-Null
    [IO.File]::WriteAllText((Join-Path $companion 'CadLink-ExportGLB.iLogicVb'), 'synthetic locator marker')
    Assert-True ((Resolve-CadLinkCompanion '' $installed) -eq $companion) 'Installed project layout was not discovered.'
    Assert-Throws { Resolve-CadLinkCompanion (Join-Path $scratch 'missing') $installed } 'Invalid explicit companion silently fell back.'
    [PSCustomObject]@{ passed = $passed; failed = 0; real_inventor_used = $false } | ConvertTo-Json
} finally {
    if ([IO.Directory]::Exists($scratch)) { [IO.Directory]::Delete($scratch, $true) }
}
