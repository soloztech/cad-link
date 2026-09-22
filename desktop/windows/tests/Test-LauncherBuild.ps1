# SPDX-License-Identifier: LGPL-3.0-or-later
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $env:OS -ne 'Windows_NT') {
    throw 'Run the executable build test with Windows PowerShell 5.1.'
}
$sourceDirectory = Split-Path $PSScriptRoot -Parent
$temporaryDirectory = Join-Path ([IO.Path]::GetTempPath()) ('cad-link-test-' + [guid]::NewGuid().ToString('N'))
New-Item -Path $temporaryDirectory -ItemType Directory | Out-Null
try {
    # Match the installer sequence: portable core first, complete EXE second.
    Add-Type -Path (Join-Path $sourceDirectory 'CadLink.Core.cs')
    $executable = Join-Path $temporaryDirectory 'CadLink.Launcher.exe'
    Add-Type -Path @((Join-Path $sourceDirectory 'CadLink.Core.cs'), (Join-Path $sourceDirectory 'CadLink.Launcher.cs')) `
        -OutputAssembly $executable -OutputType WindowsApplication `
        -ReferencedAssemblies 'System.dll', 'System.Core.dll', 'System.Xml.dll', 'System.Runtime.Serialization.dll', 'System.Windows.Forms.dll'
    $config = @{ allowedRoots = @('\\fileserver.example\CAD$') } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $temporaryDirectory 'config.json'), $config)
    $uri = 'cad-link://open?path=' + [Uri]::EscapeDataString('\\outside.example\CAD$\document.ipt')
    $stderr = Join-Path $temporaryDirectory 'error.txt'
    $process = Start-Process -FilePath $executable -ArgumentList @('--check', ('"' + $uri + '"')) `
        -Wait -PassThru -RedirectStandardError $stderr
    if ($process.ExitCode -ne 1 -or [IO.File]::ReadAllText($stderr) -notmatch 'outside the allowed network folders') {
        throw 'Executable did not reject an outside-root request through the noninteractive check path.'
    }
    Write-Output 'PASS: executable compiled and --check rejected an outside-root request before network access; no apps launched.'
}
finally {
    Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
}
