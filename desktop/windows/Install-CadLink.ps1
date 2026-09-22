# SPDX-License-Identifier: LGPL-3.0-or-later
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]] $AllowedRoot,
    [switch] $Apply
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $env:OS -ne 'Windows_NT') {
    throw 'Run this installer with Windows PowerShell 5.1 (powershell.exe), not pwsh/WSL.'
}
Add-Type -Path (Join-Path $PSScriptRoot 'CadLink.Core.cs')
$roots = @($AllowedRoot | ForEach-Object { [CadLink.RequestParser]::ValidateUncPath($_) } | Select-Object -Unique)
if ($roots.Count -eq 0) { throw 'Configure at least one allowed UNC folder.' }
$installDirectory = Join-Path $env:LOCALAPPDATA 'CAD-link'
$executable = Join-Path $installDirectory 'CadLink.Launcher.exe'
$registryPath = 'HKCU:\Software\Classes\cad-link'
$owner = 'https://github.com/soloztech/cad-link'
$ownerFile = Join-Path $installDirectory '.cad-link-owner'
$command = '"{0}" "%1"' -f $executable
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
[pscustomobject]@{
    apply = [bool]$Apply
    installation = $installDirectory
    protocol = $registryPath
    command = $command
    allowedRoots = $roots
    scope = 'Current Windows user only; no administrator permissions required'
} | ConvertTo-Json -Depth 3
if (-not $Apply) { return }

$buildDirectory = Join-Path ([IO.Path]::GetTempPath()) ('cad-link-build-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $buildDirectory | Out-Null
try {
    $builtExecutable = Join-Path $buildDirectory 'CadLink.Launcher.exe'
    Add-Type -Path @((Join-Path $PSScriptRoot 'CadLink.Core.cs'), (Join-Path $PSScriptRoot 'CadLink.Launcher.cs')) `
        -OutputAssembly $builtExecutable -OutputType WindowsApplication `
        -ReferencedAssemblies 'System.dll', 'System.Core.dll', 'System.Xml.dll', 'System.Runtime.Serialization.dll', 'System.Windows.Forms.dll'
    New-Item -ItemType Directory -Path $installDirectory -Force | Out-Null
    [IO.File]::WriteAllText($ownerFile, $owner)
    Copy-Item -LiteralPath $builtExecutable -Destination $executable -Force
    $config = @{ allowedRoots = $roots } | ConvertTo-Json -Depth 3
    [IO.File]::WriteAllText((Join-Path $installDirectory 'config.json'), $config, (New-Object Text.UTF8Encoding($false)))
    New-Item -Path $registryPath -Force | Out-Null
    Set-Item -LiteralPath $registryPath -Value 'URL:CAD-link'
    New-ItemProperty -LiteralPath $registryPath -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
    New-ItemProperty -LiteralPath $registryPath -Name 'CadLinkOwner' -Value $owner -PropertyType String -Force | Out-Null
    New-Item -Path "$registryPath\shell\open\command" -Force | Out-Null
    Set-Item -LiteralPath "$registryPath\shell\open\command" -Value $command
    Write-Output 'CAD-link installed for the current Windows user.'
}
finally {
    Remove-Item -LiteralPath $buildDirectory -Recurse -Force
}
