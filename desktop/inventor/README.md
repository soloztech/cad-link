# Inventor GLB export for CAD-link

[Guia em português](README.pt-BR.md)

This optional companion runs inside the engineer's Windows Inventor session.
It publishes a browser representation beside the saved native item:

```text
Items/
  DEMO-001/
    DEMO-001.ipt
    DEMO-001.glb
```

The Odoo server reads the resulting GLB; it does not need Inventor, a Windows
session, CAD write permissions, or an export service. The Windows URL launcher
and this exporter are separate optional companions.

## Supported environment and current validation

- Autodesk introduced native glTF/GLB export in Inventor 2023. Use a full Inventor
  installation with its glTF export translator. Inventor View, Apprentice and
  FreeCAD are not substitutes for this rule's Inventor API calls.
- The rule discovers the installed translator from its advertised extensions and
  export capability. Exactly one candidate is required unless its inspected
  class ID is configured explicitly. No translator GUID or exporter option is
  guessed. Native defaults are obtained through `HasSaveCopyAsOptions`.
- The filesystem helper has been compiled and exercised in Windows PowerShell
  against synthetic files: 17 checks, including preservation of the native file
  and old GLB after invalid output, excessive size or a locked destination.
- The complete rule also compiles against the Inventor 2024 interop assembly,
  using a stub only for the iLogic host context. That checks the referenced API
  types and VB syntax, without executing Inventor or redistributing its assembly.
- **A real Inventor export and after-save event still require validation on the
  target workstation.** Synthetic filesystem tests do not prove Inventor COM,
  texture fidelity, exported scale, assembly visibility or SMB atomic replacement.

## Set up once on each workstation

1. Place `CadLink-ExportGLB.iLogicVb` and `CadLink-InspectGLB.iLogicVb` in an external
   iLogic rules directory. The rules can be kept on a shared network location or
   deployed locally. Only maintainers should be able to modify executable rules.
2. In Inventor, use **Tools → Options → iLogic Configuration** to add that directory
   to **External Rule Directories**. Preserve existing directories and their order.
   The first directory also controls the location of the global event bindings.
3. Run the external rule **CadLink-InspectGLB** manually. It lists the actual glTF
   export translator name, class ID and extensions. It writes no CAD files and
   does not require the export configuration. Resolve missing or ambiguous
   translators before proceeding. Do not bind the inspection rule to events.
4. Copy `export.example.xml` to
   `%LOCALAPPDATA%\CAD-link\Inventor\export.xml`, creating that local directory if
   needed. Set `ItemsRoot` to the **same item directory used by Odoo**, for example
   `R:\Items` or your canonical UNC item directory. These are deployment settings,
   not values to hardcode into the rule.
5. Leave `TranslatorClassId` empty for unique discovery. Set it to the class ID
   shown in inspection only if more than one compatible translator is installed.
   Keep `MaxFileBytes` at or below the Odoo company's file size limit (50 MiB by
   default). Set `Enabled` to `true` for the manual pilot.
6. Open one saved part in its canonical `ItemsRoot\code\code.ipt` location. Update
   and save it normally, then run **CadLink-ExportGLB** manually. Confirm its GLB
   appears and opens in Odoo with the expected orientation, materials and scale.
   Repeat with one assembly whose components are all resolved, updated and saved.
   This is the point to verify write/rename rights and atomic replacement on the
   actual SMB server, including regeneration of an already existing GLB.
7. Once the pilot is correct, open **Manage → iLogic → Event Triggers**. In the
   **Parts** tab, drag **CadLink-ExportGLB** to **After Save Document**. Repeat in
   the **Assemblies** tab. Add the rule after any existing rules that intentionally
   update the document. Preserve every unrelated rule/event binding.
8. Save a part and an assembly normally, and verify the GLB time changes and the
   view refreshes in Odoo. Keep a copy of the pre-change event configuration for
   reversing the two bindings. Do not edit the event XML blindly.

Use the global **Parts** and **Assemblies** tabs, rather than **This Document**:
the former persist in `RulesOnEvents.xml` in the first external rules directory;
the latter embed bindings in a native document. A shared `RulesOnEvents.xml` can
apply the same bindings to every configured workstation. Only one maintainer
should edit it, and existing bindings must remain intact. Each Windows user keeps
their own `export.xml`, so enabling the shared rule does not enable an unconfigured
workstation to publish files.

These steps do not require adding a rule to every item, altering a template or
changing the IPJ. An installer that merges global event bindings is future work;
this package does not register events or relax iLogic security automatically.

## What happens on each save

- Only a saved IPT or IAM in the exact configured `code\code.ext` layout qualifies.
  Other locations, documents and temporary/new files are skipped. A code with
  both an IPT and IAM is rejected because both would overwrite the same GLB.
- The rule checks that the document and referenced documents are saved and up to
  date, and refuses unresolved non-suppressed references. It does not call `Save`,
  `Save2`, `Update`, change representations or modify native CAD properties.
- The translator runs synchronously on Inventor's own thread. It writes to a
  random `.cad-link-export-...` staging subdirectory of the item folder, so the
  Odoo file listing cannot expose a half-written top-level GLB.
- An exclusive `.cad-link-export.lock` handle prevents overlapping exports of the
  same item, including reentrant events. The lock file is removed on handle close.
- After export, the rule checks the GLB header, declared length, JSON chunk bounds
  and maximum size. It also compares the source and dependency file sizes/times
  and current document state before publishing. These checks are not a complete
  glTF schema validator or a distributed revision lock.
- It moves a first GLB into place or uses `File.Replace` for an existing GLB. There
  is no delete-then-copy fallback. If the share does not support the replacement,
  another program holds an incompatible lock, the source changed or translation
  fails, the previous GLB stays in place. Staging is cleaned up when possible.
- Status and errors go to Inventor's status bar and the local
  `%LOCALAPPDATA%\CAD-link\Inventor\export.log`. Export exceptions are caught so
  they do not cancel the already completed native save. They do not suppress an
  error from an unrelated rule. The log rotates at approximately 1 MiB.

## Scope and limitations

Saving a part refreshes that part's GLB. It **does not refresh every parent
assembly automatically**. Open, update and save the assembly to regenerate its
GLB. A future dependency queue can address that separately; this version does not
claim recursive freshness from the GLB timestamp alone.

The exporter uses the document state supplied by Inventor and native translation
defaults. It does not select a particular design view, positional representation,
model state, level of detail or material override. Decide a standard representation
for each item and validate it in the pilot. GLB includes the textures emitted by
the translator, but appearances without suitable texture assets cannot be made
photorealistic by the viewer alone. A browser GLB is a derived display, not a
parametric substitute for the Inventor source.

Large assemblies may make saving noticeably slower. Begin with selected
workstations; do not move Inventor COM calls to a generic background thread or
Windows service. Concurrent editing of the same native files still requires the
engineering team's own file coordination; the export lock protects GLB publication,
not native editing. A computer that crashes can leave a staging directory behind.

To pause exports, set `Enabled` to `false`. To remove the automatic behavior, remove
only the two CAD-link bindings in Event Triggers. Existing GLBs remain available.
Keep native CAD and derived files backed up under your normal repository policy.

## Tests

Run from Windows PowerShell 5.1:

```powershell
.\tests\Test-ExportFiles.ps1
```

Tests use a disposable local temporary directory and synthetic bytes. They never
open Inventor, contact Odoo, register events or write the engineering repository.

## Autodesk references

- [Inventor 2023 translator enhancements](https://help.autodesk.com/cloudhelp/2024/ENU/Inventor-WhatsNew/files/GUID-EF5ADBDC-BB7F-4CB2-B991-C4645F8C4A18.htm)
- [TranslatorAddIn API](https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/TranslatorAddIn.htm)
- [SaveCopyAs API](https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/TranslatorAddIn_SaveCopyAs.htm)
- [Translator options](https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/TranslatorSettings.htm)
- [Event trigger configuration and sharing](https://help.autodesk.com/cloudhelp/2022/ENU/Inventor-iLogic/files/GUID-B14A47F4-81D2-4627-A973-2BC7F790DF89.htm)
- [After Save Document event](https://help.autodesk.com/cloudhelp/2016/ENU/Inventor-Help/files/GUID-A5262025-BB42-4707-8BA0-C0ED830FF3BD.htm)
- [Advanced iLogic rule syntax](https://help.autodesk.com/cloudhelp/2021/ENU/Inventor-iLogic/files/GUID-32B66838-22E4-4A0A-B5BB-862350C76B36.htm)
