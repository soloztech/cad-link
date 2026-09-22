# Optional Windows launcher

CAD-link can list and download documents without this component. Install the
launcher for **Open on network**, **Open item folder**, and **Show in folder**.
It opens the original shared document using the current Windows user's account.
It does not copy the document, connect to Odoo, install Inventor, or store passwords.

## Install for the current user

Requirements: Windows, Windows PowerShell 5.1, .NET Framework, and an existing
Windows association for each document type. Use `powershell.exe`, not `pwsh`, for
the installer. No administrator account, WSL, Python, or Visual Studio is needed.
The installer builds a small AnyCPU .NET Framework executable from the included
C# source, suitable for supported Windows x64 and ARM64 systems with the runtime.

Download this repository, then run these commands in **Windows PowerShell** from
`desktop\windows`. Replace the example share with the permitted CAD root.

```powershell
# Show the installation plan; does not change the registry or installation.
.\Install-CadLink.ps1 -AllowedRoot '\\fileserver.example\CAD$'

# Install the reviewed configuration for this Windows user.
.\Install-CadLink.ps1 -AllowedRoot '\\fileserver.example\CAD$' -Apply
```

Multiple roots can be passed as a PowerShell array:

```powershell
.\Install-CadLink.ps1 -AllowedRoot @('\\fileserver.example\CAD$', '\\archive.example\CAD') -Apply
```

If Windows blocks a downloaded script, review the files and follow your
organization's script policy. The installer does not change execution policies.
When working from WSL or another UNC location, copy the reviewed launcher files
to a local Windows folder before running them; Windows may classify UNC scripts
as remote and require signatures even when the same local script is permitted.
Run it again with the complete root list to update the launcher/configuration.
The browser may ask permission to open CAD-link; allow it only on your trusted
Odoo site. Some managed browsers may require an administrator's protocol policy.

The installer writes only:

- `%LOCALAPPDATA%\CAD-link\CadLink.Launcher.exe`
- `%LOCALAPPDATA%\CAD-link\config.json` (the explicit UNC root list)
- `%LOCALAPPDATA%\CAD-link\.cad-link-owner` (installation ownership marker)
- `HKCU\Software\Classes\cad-link` (per-user URL handler)

The configuration is machine-specific and belongs outside the public repository.
An existing protocol registered by a different application is not overwritten.
Browser protocol registration is per user: installing under a different Windows
account will not activate it for the engineer's browser session.

## Actions and protocol

```text
cad-link://open?path=<percent-encoded UNC path>
cad-link://folder?path=<percent-encoded UNC path>
```

Encode the complete UNC path with JavaScript `encodeURIComponent` or .NET
`Uri.EscapeDataString`. Do not add extra parameters or a slash before `?path`.
The launcher decodes once, validates the request, then checks target attributes.

| Action | Target | Behavior |
| --- | --- | --- |
| `open` | Allowed CAD/PDF file | Opens the original through the Windows `open` association. |
| `folder` | Directory | Opens that directory in Explorer. |
| `folder` | Allowed CAD/PDF file | Opens Explorer and selects that file. |

Allowed extensions: `.ipt`, `.iam`, `.idw`, `.dwg`, `.dxf`, `.pdf`, `.step`, `.stp`,
`.iges`, `.igs`, `.sat`, `.stl`, `.obj`, `.mtl`, `.glb`, `.gltf`.
For Inventor sources, set the Windows default application to the appropriate
Inventor version. If a viewer is associated instead, that viewer will open.
No Inventor API is called and the active Inventor project is not switched.

Windows enforces share and filesystem permissions independently of Odoo. The
launcher cannot grant network access or bypass those permissions. A user who can
download through Odoo might not be able to open the share in Explorer.

## Validation and limits

- The URL handler invokes an executable directly. It never interpolates the URL
  into PowerShell, `cmd.exe`, or an evaluated command string.
- Requests require the exact scheme/action and one encoded `path` parameter.
  Extra process arguments are rejected. Only explicitly allowed UNC root
  descendants are accepted, using case-insensitive component boundaries.
- Local disks, mapped drive letters, device paths, traversal, alternate data
  streams, Windows reserved names, trailing dots/spaces, and script/executable/
  shortcut extensions are rejected. Paths must be shorter than 260 characters;
  server names must be ASCII hostnames/IPv4 addresses. Supplementary Unicode
  characters are not supported in this initial launcher.
- Reparse points are rejected when Windows exposes that attribute on the share
  or an intermediate component. This is a best-effort check with a check/open
  race; share administrators must keep these trusted CAD roots free of junctions
  and symbolic links. DFS redirects and server-side aliases are not confined by
  a client-side string check.
- The launcher cannot authenticate the web page that invoked a custom protocol.
  Any application/site can request an allowed path, subject to browser prompts
  and the same Windows account's access. The root list is an accidental-use
  safeguard, not a boundary against the Windows user who owns the configuration.
- CAD documents can have dependencies and application automation features. Keep
  allowed roots trusted and CAD applications updated. Windows file associations
  are administered separately; this component does not sandbox the CAD app.

Microsoft documents opening associated documents through
[`ProcessStartInfo.UseShellExecute`](https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-diagnostics-processstartinfo-useshellexecute)
and compiling with
[`Add-Type` in Windows PowerShell 5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/add-type?view=powershell-5.1).

## Tests

Run in a fresh PowerShell process; no Pester dependency is required:

```powershell
powershell.exe -NoProfile -File .\tests\Test-RequestParser.ps1
powershell.exe -NoProfile -File .\tests\Test-LauncherBuild.ps1
```

The parser tests also work with `pwsh`: they compile only the portable core,
perform no network I/O, and launch no applications. Installer/executable smoke
tests require Windows PowerShell 5.1. The build test compiles the executable and
checks rejection of an outside-root URI before any network access. Testing valid
requests also requires an accessible test share. After
installation, use Odoo's **Open item folder** and **Show in folder** on a known
document before testing **Open on network** in the associated CAD application.

To validate a configured request, including network access and visible reparse
attributes, without opening an application:

```powershell
$uri = 'cad-link://folder?path=' + [Uri]::EscapeDataString('\\fileserver.example\CAD$\Items\000001')
$exe = Join-Path $env:LOCALAPPDATA 'CAD-link\CadLink.Launcher.exe'
$process = Start-Process -FilePath $exe -ArgumentList @('--check', ('"' + $uri + '"')) -Wait -PassThru
$process.ExitCode # 0 = valid and accessible; 1 = invalid or inaccessible
```

`--check` is a local command-line option, not a URI action. It can emit details
to standard output/error when those streams are redirected by a test runner.

## Uninstall

```powershell
.\Uninstall-CadLink.ps1          # plan
.\Uninstall-CadLink.ps1 -Apply   # remove this user's handler/config/executable
```

The uninstall script leaves network documents, application associations, and
unknown files in the installation folder unchanged.
