# MyGO desktop editor

The desktop GUI uses MyGO v0.9.0 native widgets with a Nord palette. MyGO draws the interface; Goja runs the shared save algorithms. The executable does not start a browser, WebView, Python interpreter or local server.

## Build and run

These commands target Windows 10/11 x64; other platforms have not been validated for this editor. Install Go 1.27.3 or later, Node.js 20 or later, and Python 3.10 or later. Obtain the repository source and open PowerShell at its root. No `npm install` is needed; the build fetches esbuild and Go dependencies.

```powershell
npm run build:mygo
.\start.bat
```

The output is `dist/mygo/RF4S Save Editor.exe`. It embeds the JavaScript bundle, fonts and available curated game references. End users do not need the build tools or a game installation. `start.bat` checks this build first, with existing Qt builds kept as fallbacks.

For source development:

```powershell
npm run build:mygo-core
npm run build:mygo-assets
npm run start:mygo
```

Rebuild the core after changing JavaScript, and repack assets after changing fonts, translations or `builtin/`. The commands use `-mod=mod` because this repository's existing `vendor/` holds Python references, not vendored Go modules. Do not run `go mod vendor` over it.

## Offline assets

Fonts and their OFL notices are in `web/assets/fonts/`. `scripts/prepare_mygo.py` also copies the English/Chinese caption catalog and, when present, `builtin/references.json.gz` and `builtin/icons.zip` into the embedded asset archive.

Generated game references are not tracked in Git. To create them from your own game installation:

```powershell
python -m pip install Pillow
python -m scripts.generate_builtin "<game folder>"
npm run build:mygo
```

Asset preparation reads game files without modifying them. Without generated references, the editor can open saves and edit calendar/player fields, skills, relationships, orders, soil, system records and expert fields. Adding/replacing items, equipment presets, effect previews and recipe lists require the appropriate reference tables. The build prints a notice for each missing asset.

**Save overview** can import extracted item/equipment/use/upgrade `.bin` tables, recipe `.bin` tables, localized TEXT name tables and `emdeb.bin` symbols. Imports last for the current session; they do not replace the bundled files or supply missing icon images. The generation command above is the supported way to prepare references from a game installation. To refresh them, regenerate `builtin/` and rebuild.

## Controls and save safety

Use **Open save** to choose a slot or `rf4_sys.sav`. No personal save is loaded automatically. **Try synthetic demo** opens generated data with export disabled.

The navigation includes calendar/player values, bag/storage and equipment, skills/recipes, friendship, dating/nicknames, people/monsters, marriage, roster creation, orders, soil, trophies, system names/unlocks, story tools, raw fields, references, export and backups. Experimental editors retain their risk acknowledgements and validation in the shared save core.

Typing a value or changing a checkbox creates a draft in the visible form. **Apply changes** commits it to the in-memory save; **Clear draft** restores the form's last applied values. Valid drafts also apply as one undoable edit before switching records or pages, or exporting. Invalid drafts stay visible and block those actions. Interface and game-name language selectors preserve the draft and stored IDs. Chinese captions are available, though some helper text remains English.

**Export edited save** writes PC output to `%APPDATA%\Rune Factory 4 Special` after creating a same-folder backup. Under **Review & export**, choose `rf4_sNN.sav` for a slot save or `rf4_sys.sav` for a system save. A confirmation asks you to close the game before writing. Successful exports and restores retain up to ten managed backups for that target; cleanup failures are reported without hiding a successful save.

**Save as…** writes a separate copy or extracted Switch output. PC/Switch conversion requires explicit consent. **Backups & rollback** previews a backup, checks that it has not changed since review, backs up the current disk save and restores the selected bytes after confirmation.

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Open save |
| Ctrl+S | Export to the game folder |
| Ctrl+Shift+S | Save as |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Ctrl+Shift+L | Learn all loaded recipes |

Text fields use their own undo while focused. The window supports 640×480; compact windows use a section dropdown instead of the sidebar. Long forms and the inventory grid scroll separately.

## Validation

Run from the repository root. `test:mygo` prepares the core and assets before running Go tests; the screenshot command uses those prepared files. Generated references are needed to exercise the complete item/equipment/recipe tools.

```powershell
npm test
npm run test:mygo
go run -mod=mod . --screenshot dist/mygo/preview.png
```

The Go tests exercise native controls at desktop and compact sizes, draft validation, atomic edits, undo/redo, PC/Switch output, system names/unlocks and backup retention/restoration. They use synthetic saves and temporary directories. The screenshot command renders the synthetic inventory view without opening a window or writing a game save.

The Qt entry point (`desktop.py`) and browser editor remain available. Their existing documentation and tests apply to those editions. No in-game acceptance testing is implied by the automated checks.
