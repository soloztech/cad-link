# SPDX-License-Identifier: LGPL-3.0-or-later
# Compile against the local Inventor API with iLogic's implicit imports.
# The proprietary interop assembly is supplied by an installed Inventor; never
# copy it into this repository. No Inventor process or COM instance is started.
#Requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$InventorInteropPath
)
$ErrorActionPreference = 'Stop'
$interop = [IO.Path]::GetFullPath($InventorInteropPath)
if (-not [IO.File]::Exists($interop) -or [IO.Path]::GetFileName($interop) -ne 'Autodesk.Inventor.Interop.dll') {
    throw 'Supply the Autodesk.Inventor.Interop.dll from the Inventor installation.'
}
$rulePath = Join-Path $PSScriptRoot '..\CadLink-ExportGLB.iLogicVb'
$rule = [IO.File]::ReadAllText($rulePath)
$source = "Imports System`nImports Inventor`nImports System.Windows.Forms`n" + [Text.RegularExpressions.Regex]::Replace($rule, '(?m)^AddReference [^\r\n]+\r?\n', '')
$context = @'
Class ThisRule
    Public ThisApplication As Inventor.Application
    Public ThisDoc As CadLinkCompileTestDocument
    Public RuleArguments As CadLinkCompileTestArguments
'@
$source = $source.Replace('Class ThisRule', $context)
$source += @'

Public Class CadLinkCompileTestDocument
    Public Document As Inventor.Document
End Class
Public Class CadLinkCompileTestArguments
    Public Function Exists(ByVal name As String) As Boolean
        Return False
    End Function
    Default Public ReadOnly Property Item(ByVal name As String) As Object
        Get
            Return Nothing
        End Get
    End Property
End Class
'@
Add-Type -TypeDefinition $source -Language VisualBasic -ReferencedAssemblies @($interop, 'System.dll', 'System.Core.dll', 'System.Xml.dll', 'System.Windows.Forms.dll')
[PSCustomObject]@{
    compiled = $true
    inventor_com_executed = $false
    ilogic_context_stubbed = $true
    implicit_imports = @('System', 'Inventor', 'System.Windows.Forms')
    rule_sha256 = (Get-FileHash -LiteralPath $rulePath -Algorithm SHA256).Hash.ToLowerInvariant()
    interop_sha256 = (Get-FileHash -LiteralPath $interop -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json
