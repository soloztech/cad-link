# SPDX-License-Identifier: LGPL-3.0-or-later
# Windows PowerShell 5.1. Exercises the actual VB filesystem helper, without CAD.
$ErrorActionPreference = 'Stop'
$rulePath = Join-Path $PSScriptRoot '..\CadLink-ExportGLB.iLogicVb'
$rule = [IO.File]::ReadAllText($rulePath)
$helper = $rule.Substring($rule.IndexOf('Public Class CadLinkExportFiles'))
$source = "Imports System`nImports System.IO`nImports System.Collections.Generic`n" + $helper
Add-Type -TypeDefinition $source -Language VisualBasic
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('cad-link-export-test-' + [Guid]::NewGuid().ToString('N'))
$passed = 0

function Assert-True([bool]$condition, [string]$description) {
    if (-not $condition) { throw $description }
    $script:passed++
}
function Assert-Throws([scriptblock]$action, [string]$description) {
    $threw = $false
    try { & $action } catch { $threw = $true }
    Assert-True $threw $description
}
function Write-Glb([string]$path, [string]$generator) {
    $json = '{"asset":{"version":"2.0","generator":"' + $generator + '"}}'
    while (($json.Length % 4) -ne 0) { $json += ' ' }
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $writer = New-Object IO.BinaryWriter([IO.File]::Create($path))
    try {
        $writer.Write([uint32]0x46546c67)
        $writer.Write([uint32]2)
        $writer.Write([uint32](20 + $bytes.Length))
        $writer.Write([uint32]$bytes.Length)
        $writer.Write([uint32]0x4e4f534a)
        $writer.Write($bytes)
    } finally { $writer.Dispose() }
}

try {
    $items = Join-Path $scratch 'Items'
    $item = Join-Path $items 'DEMO-001'
    [IO.Directory]::CreateDirectory($item) | Out-Null
    $native = Join-Path $item 'DEMO-001.ipt'
    [IO.File]::WriteAllText($native, 'synthetic native sentinel')
    $nativeHash = (Get-FileHash -LiteralPath $native).Hash
    Assert-True ([CadLinkExportFiles]::EligibleSource($items, $native) -eq $native) 'Canonical source was rejected.'
    Assert-True ($null -eq [CadLinkExportFiles]::EligibleSource($items + '-other', $native)) 'Prefix lookalike root was accepted.'
    $other = Join-Path $item 'WRONG.ipt'
    [IO.File]::WriteAllText($other, 'synthetic')
    Assert-True ($null -eq [CadLinkExportFiles]::EligibleSource($items, $other)) 'Wrong source basename was accepted.'
    Assert-Throws { [CadLinkExportFiles]::EligibleSource('', $native) } 'An empty root was accepted.'
    $assembly = [IO.Path]::ChangeExtension($native, '.iam')
    [IO.File]::WriteAllText($assembly, 'synthetic assembly')
    Assert-Throws { [CadLinkExportFiles]::EligibleSource($items, $native) } 'Ambiguous IPT/IAM output was accepted.'
    [IO.File]::Delete($assembly)

    $stage = Join-Path $item '.cad-link-export-synthetic'
    [IO.Directory]::CreateDirectory($stage) | Out-Null
    $candidate = Join-Path $stage 'DEMO-001.glb'
    $output = Join-Path $item 'DEMO-001.glb'
    Write-Glb $candidate 'first'
    [CadLinkExportFiles]::Publish($candidate, $output, 1048576)
    Assert-True ([IO.File]::Exists($output) -and -not [IO.File]::Exists($candidate)) 'First publication failed.'
    $firstHash = (Get-FileHash -LiteralPath $output).Hash
    [IO.File]::WriteAllText($candidate, 'interrupted or invalid GLB')
    Assert-Throws { [CadLinkExportFiles]::Publish($candidate, $output, 1048576) } 'Invalid GLB replaced the previous export.'
    Assert-True ((Get-FileHash -LiteralPath $output).Hash -eq $firstHash) 'Previous GLB changed after rejected export.'
    Write-Glb $candidate 'second'
    Assert-Throws { [CadLinkExportFiles]::Publish($candidate, $output, 24) } 'Oversize GLB was published.'
    Assert-True ((Get-FileHash -LiteralPath $output).Hash -eq $firstHash) 'Previous GLB changed after oversize export.'
    Assert-Throws { [CadLinkExportFiles]::Publish($candidate, $native, 1048576) } 'Native output path was accepted.'
    $lock = [IO.File]::Open($output, 'Open', 'Read', 'None')
    try {
        Assert-Throws { [CadLinkExportFiles]::Publish($candidate, $output, 1048576) } 'Locked GLB unexpectedly replaced.'
    } finally { $lock.Dispose() }
    Assert-True ((Get-FileHash -LiteralPath $output).Hash -eq $firstHash) 'Locked output changed.'
    [CadLinkExportFiles]::Publish($candidate, $output, 1048576)
    Assert-True ((Get-FileHash -LiteralPath $output).Hash -ne $firstHash) 'Atomic replacement did not publish new bytes.'
    Assert-True ((Get-FileHash -LiteralPath $native).Hash -eq $nativeHash) 'Original native file was modified.'
    $before = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
    $after = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
    $before[$native] = '123:456'
    $after[$native] = '123:456'
    Assert-True ([CadLinkExportFiles]::SameSnapshot($before, $after)) 'Identical snapshot rejected.'
    $after[$native] = '124:457'
    Assert-True (-not [CadLinkExportFiles]::SameSnapshot($before, $after)) 'Changed source snapshot accepted.'
    [PSCustomObject]@{ passed = $passed; failed = 0; inventor_com_tested = $false } | ConvertTo-Json
} finally {
    if ([IO.Directory]::Exists($scratch)) { [IO.Directory]::Delete($scratch, $true) }
}
