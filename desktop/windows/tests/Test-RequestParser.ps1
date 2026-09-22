# SPDX-License-Identifier: LGPL-3.0-or-later
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -Path (Join-Path (Split-Path $PSScriptRoot -Parent) 'CadLink.Core.cs')
$script:checks = 0
$roots = [string[]]@('\\fileserver.example\CAD$')

function New-TestUri([string] $Action, [string] $Path) {
    return 'cad-link://' + $Action + '?path=' + [Uri]::EscapeDataString($Path)
}
function Assert-Accepted([string] $Uri, [string] $ExpectedPath, [string[]] $AllowedRoots = $roots) {
    $request = [CadLink.RequestParser]::Parse($Uri, $AllowedRoots)
    if ($request.Path -cne $ExpectedPath) { throw "Incorrect literal path: $Uri" }
    $script:checks++
}
function Assert-Rejected([string] $Uri, [string[]] $AllowedRoots = $roots) {
    $rejected = $false
    try { [CadLink.RequestParser]::Parse($Uri, $AllowedRoots) | Out-Null }
    catch { $rejected = $true }
    if (-not $rejected) { throw "Unsafe request accepted: $Uri" }
    $script:checks++
}

foreach ($path in @(
    '\\fileserver.example\CAD$\Items\000001\000001.ipt',
    '\\FILESERVER.EXAMPLE\cad$\Items\000001\000001.IAM',
    '\\fileserver.example\CAD$\Items\Space and & plus+ comma, (parenthesis)\drawing.pdf',
    '\\fileserver.example\CAD$\Items\literal$(whoami)`name%20file.ipt',
    ('\\fileserver.example\CAD$\Items\A' + [char]0x00E7 + 'o\drawing.idw')
)) {
    Assert-Accepted (New-TestUri 'open' $path) $path
}
Assert-Accepted (New-TestUri 'folder' $roots[0]) $roots[0]
Assert-Accepted (New-TestUri 'folder' ($roots[0] + '\Items\000001')) ($roots[0] + '\Items\000001')
Assert-Accepted (New-TestUri 'folder' ($roots[0] + '\Items\000001\000001.ipt')) ($roots[0] + '\Items\000001\000001.ipt')
$path = '\\second\Documents\000001.pdf'
Assert-Accepted (New-TestUri 'open' $path) $path ([string[]]@($roots[0], '\\second\Documents'))

foreach ($path in @(
    '\\evil.example\CAD$\secret.ipt',
    '\\fileserver.example\CAD$-other\secret.ipt',
    '\\fileserver.example\CAD$\..\other\secret.ipt',
    '\\fileserver.example\CAD$\.\document.ipt',
    '\\fileserver.example\CAD$\folder.\document.ipt',
    '\\fileserver.example\CAD$\folder \document.ipt',
    '\\fileserver.example\CAD$\\document.ipt',
    '\\fileserver.example\CAD$\document.ipt:payload.exe',
    '\\fileserver.example\CAD$\document.ipt::$DATA',
    '\\fileserver.example\CAD$\document.ipt.exe',
    '\\fileserver.example\CAD$\shortcut.lnk',
    '\\fileserver.example\CAD$\shortcut.url',
    '\\fileserver.example\CAD$\script.ps1',
    '\\fileserver.example\CAD$\script.bat',
    '\\fileserver.example\CAD$\script.cmd',
    '\\fileserver.example\CAD$\project.ipj',
    '\\fileserver.example\CAD$\CON\document.ipt',
    '\\fileserver.example\CAD$\nul.ipt',
    '\\fileserver.example\CAD$\COM1.ipt',
    '\\fileserver.example\CAD$\*\document.ipt',
    '\\fileserver.example\CAD$\quote" -Command evil.ipt',
    "\\fileserver.example\CAD`$\line`nfeed.ipt",
    '\\?\UNC\fileserver.example\CAD$\document.ipt',
    '\\.\fileserver.example\CAD$\document.ipt',
    '//fileserver.example/CAD$/document.ipt',
    'C:\Users\User\document.ipt',
    'R:\Items\document.ipt',
    '\\fileserver.example\CAD$\',
    '\\fileserver.example',
    ('\\fileserver.example\CAD$\' + ('x' * 240) + '.ipt')
)) { Assert-Rejected (New-TestUri 'open' $path) }

$valid = New-TestUri 'open' '\\fileserver.example\CAD$\document.ipt'
Assert-Accepted ($valid.Replace('//open?', '//open/?')) '\\fileserver.example\CAD$\document.ipt'
$folderUri = New-TestUri 'folder' '\\fileserver.example\CAD$\Items\000001'
Assert-Accepted ($folderUri.Replace('//folder?', '//folder/?')) '\\fileserver.example\CAD$\Items\000001'
foreach ($uri in @(
    ($valid + '&path=other'),
    ($valid + '&command=evil'),
    ($valid + '#fragment'),
    ($valid + '" "extra argument'),
    ($valid + '%00'),
    ($valid + '%GG'),
    ($valid + '%'),
    ($valid.Replace('cad-link:', 'file:')),
    ($valid.Replace('//open?', '//open//?')),
    ($valid.Replace('//open?', '//open/other?')),
    ($valid.Replace('//open?', '//execute?')),
    ($valid.Replace('//open?', '//user@open?')),
    ($valid.Replace('//open?', '//open:123?')),
    ($valid.Replace('?path=', '?Path=')),
    'cad-link://open?path=',
    'cad-link://open?path=\\fileserver.example\CAD$\document.ipt',
    'cad-link://open?path=..%5Cdocument.ipt',
    'cad-link://open?path=x+y',
    ''
)) { Assert-Rejected $uri }
Assert-Rejected $valid ([string[]]@())
Assert-Rejected $valid ([string[]]@('C:\CAD'))
Assert-Rejected $valid ([string[]]@('\\fileserver.example\CAD$\..\'))

# Folder actions cannot turn a script into an executable. The runtime validates
# the type after checking whether the target is a directory or a regular file.
foreach ($path in @('document.ps1', 'document.exe', 'document.lnk', 'document.pdf.exe')) {
    if ([CadLink.RequestParser]::IsAllowedFile($path)) { throw "Forbidden file type: $path" }
    $script:checks++
}

$request = [CadLink.RequestParser]::Parse($valid, $roots)
$safeAttributes = [Func[string, IO.FileAttributes]] {
    param([string] $path)
    if ($path.EndsWith('.ipt')) { return [IO.FileAttributes]::Normal }
    return [IO.FileAttributes]::Directory
}
[CadLink.TargetValidator]::Check($request, $safeAttributes) | Out-Null
$script:checks++
foreach ($reparseTarget in @($roots[0], ($roots[0] + '\Items'))) {
    $nestedRequest = [CadLink.RequestParser]::Parse((New-TestUri 'open' ($roots[0] + '\Items\000001.ipt')), $roots)
    $reparseAttributes = [Func[string, IO.FileAttributes]] {
        param([string] $path)
        if ($path -eq $reparseTarget) { return [IO.FileAttributes]::Directory -bor [IO.FileAttributes]::ReparsePoint }
        if ($path.EndsWith('.ipt')) { return [IO.FileAttributes]::Normal }
        return [IO.FileAttributes]::Directory
    }
    $rejected = $false
    try { [CadLink.TargetValidator]::Check($nestedRequest, $reparseAttributes) | Out-Null }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Reparse share/ancestor was accepted.' }
    $script:checks++
}
$scriptRequest = [CadLink.RequestParser]::Parse((New-TestUri 'folder' ($roots[0] + '\script.ps1')), $roots)
$fileAttributes = [Func[string, IO.FileAttributes]] { param([string] $path) return [IO.FileAttributes]::Normal }
$rejected = $false
try { [CadLink.TargetValidator]::Check($scriptRequest, $fileAttributes) | Out-Null }
catch { $rejected = $true }
if (-not $rejected) { throw 'Folder action accepted a script file.' }
$script:checks++
Write-Output "PASS: $script:checks launcher parser checks; no network requests or applications launched."
