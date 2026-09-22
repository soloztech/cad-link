# SPDX-License-Identifier: LGPL-3.0-or-later
#Requires -Version 5.1
[CmdletBinding()]
param([switch] $Apply)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT') { throw 'Run this script in Windows.' }
$installDirectory = Join-Path $env:LOCALAPPDATA 'CAD-link'
$registryPath = 'HKCU:\Software\Classes\cad-link'
$owner = 'https://github.com/soloztech/cad-link'
$ownerFile = Join-Path $installDirectory '.cad-link-owner'
if (Test-Path -LiteralPath $registryPath) {
    $previousOwner = Get-ItemPropertyValue -LiteralPath $registryPath -Name 'CadLinkOwner' -ErrorAction SilentlyContinue
    if ($previousOwner -ne $owner) { throw 'The cad-link protocol belongs to another application; no changes made.' }
}
if (Test-Path -LiteralPath $installDirectory) {
    $existingItem = Get-Item -LiteralPath $installDirectory
    if (-not $existingItem.PSIsContainer -or ($existingItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'The installation location must be an ordinary directory.'
    }
    if (@(Get-ChildItem -LiteralPath $installDirectory -Force).Count -gt 0 -and
        (-not (Test-Path -LiteralPath $ownerFile) -or [IO.File]::ReadAllText($ownerFile) -ne $owner)) {
        throw 'The installation directory contains files not owned by CAD-link; no changes made.'
    }
}
[pscustomobject]@{ apply = [bool]$Apply; installation = $installDirectory; protocol = $registryPath } | ConvertTo-Json
if (-not $Apply) { return }
if (Test-Path -LiteralPath $registryPath) { Remove-Item -LiteralPath $registryPath -Recurse -Force }
foreach ($name in @('CadLink.Launcher.exe', 'config.json', '.cad-link-owner')) {
    $path = Join-Path $installDirectory $name
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}
if ((Test-Path -LiteralPath $installDirectory) -and @(Get-ChildItem -LiteralPath $installDirectory -Force).Count -eq 0) {
    Remove-Item -LiteralPath $installDirectory
}
Write-Output 'CAD-link removed for the current Windows user. Network documents were not changed.'
