package main

import (
	"encoding/json"
	"fmt"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/egoist/mygo"
	"github.com/egoist/mygo/ui"
)

func targetChoices() []Choice {
	options := []Choice{{"Choose target save slot", ""}}
	for i := 0; i < 40; i++ {
		name := fmt.Sprintf("rf4_s%02d.sav", i)
		options = append(options, Choice{name, name})
	}
	return append(options, Choice{"rf4_sys.sav", "rf4_sys.sav"})
}

func (e *Editor) review(c *ui.Context) {
	if e.state == nil {
		e.note(c, "Open a save first.")
		return
	}
	e.note(c, "Export writes to the game save folder and creates a backup there first. Save as is available for copies and other platforms.")
	e.card(c, "Changes in memory", func() {
		ui.Text(c, fmt.Sprintf("%d changed bytes · %d undoable edits", e.state.ChangedBytes, e.state.Undo)).TextColor(e.theme.Accent)
		var changes []struct {
			Offset        int
			Before, After []int
		}
		if err := e.core.Call("changes", nil, &changes); err == nil {
			lines := []string{}
			for i, change := range changes {
				if i >= 100 {
					lines = append(lines, fmt.Sprintf("First 100 of %d ranges. The JSON report includes all.", len(changes)))
					break
				}
				lines = append(lines, fmt.Sprintf("0x%05X: %v → %v", change.Offset, change.Before, change.After))
			}
			text := strings.Join(lines, "\n")
			if text == "" {
				text = e.tr("No byte changes")
			}
			ui.TextArea(c, &text).ReadOnly(true).Height(180).Font("monospace").Label("Byte changes")
		}
		e.note(c, "Pending edits are applied automatically when exporting.")
	})
	e.card(c, "Export options", func() {
		ui.Text(c, e.tr("Target save file")).FontSize(13)
		e.choose(c, "Target save file", &e.target, targetChoices(), false).FillWidth()
		if e.state.Kind == "slot" {
			ui.Text(c, e.tr("Output platform")).FontSize(13)
			e.choose(c, "Output platform", &e.platform, []Choice{{"Keep source format", "keep"}, {"PC (experimental if converting)", "pc"}, {"Switch (experimental if converting)", "switch"}}, false).FillWidth()
			ui.Checkbox(c, &e.conversion, e.tr("I accept experimental PC / Switch conversion risks"))
			ui.Text(c, e.tr("Gender on export")).FontSize(13)
			e.choose(c, "Gender on export", &e.gender, []Choice{{"Keep edited gender", "keep"}, {"Match original gender", "original"}, {"Male · Lest", "male"}, {"Female · Frey", "female"}}, false).FillWidth()
			ui.Checkbox(c, &e.resetAppearance, e.tr("Also reset appearance, portrait and outfit"))
			ui.Checkbox(c, &e.resetDating, e.tr("Clear incompatible dating and their special nicknames (keep friendship)"))
			if e.resetDating {
				gender := e.gender
				if gender == "original" && len(e.original) > 0x36 {
					if e.original[0x36] == 0 {
						gender = "male"
					} else if e.original[0x36] == 1 {
						gender = "female"
					}
				}
				var people []struct{ Name string }
				if err := e.core.Call("datingCleanup", map[string]any{"gender": gender}, &people); err != nil {
					e.note(c, err.Error())
				} else {
					names := []string{}
					for _, p := range people {
						names = append(names, p.Name)
					}
					e.note(c, "Will clear dating / reset addresses: "+strings.Join(names, ", "))
				}
			}
		}
		ui.Row(c).Wrap().Gap(8).Children(func() {
			ui.PrimaryButton(c, e.tr("Export edited save")).Disabled(e.demo).OnClick(func() { e.export(false) })
			ui.Button(c, e.tr("Save as…")).Disabled(e.demo).OnClick(func() { e.export(true) })
			ui.Button(c, e.tr("Download change report")).OnClick(func() {
				if e.apply() {
					e.saveJSON("changes", "save.changes.json")
				}
			})
			ui.Button(c, e.tr("Restore original in memory")).OnClick(func() {
				e.confirm("Discard unexported edits and drafts?", func() { e.fail(e.core.Call("reset", nil, nil)); e.fail(e.refresh(false)) })
			})
		})
	})
	e.note(c, "Back up your entire save folder and close the game. Keep the game closed until export finishes. Handle Steam Cloud conflicts separately.")
}

func (e *Editor) buildOutput() ([]byte, error) {
	if e.state == nil {
		return nil, fmt.Errorf("open a save first")
	}
	if e.demo {
		return nil, fmt.Errorf("demo export is disabled")
	}
	platform, gender := e.state.Platform, "keep"
	if e.state.Kind == "slot" {
		if e.platform != "keep" {
			platform = e.platform
		}
		gender = e.gender
	}
	if platform != e.state.Platform && !e.conversion {
		return nil, fmt.Errorf("acknowledge experimental conversion before exporting")
	}
	return e.core.Bytes("build", map[string]any{"platform": platform, "gender": gender, "experimental": e.conversion, "repair": true,
		"resetAppearance": e.state.Kind == "slot" && e.resetAppearance, "resetDating": e.state.Kind == "slot" && e.resetDating})
}

func (e *Editor) export(saveAs bool) {
	if e.busy || e.state == nil || e.demo {
		return
	}
	if !saveAs && (!saveName.MatchString(e.target) || (e.target == "rf4_sys.sav") != (e.state.Kind == "system")) {
		e.navigate("review")
		e.fail(fmt.Errorf("choose a target save file matching the loaded save type"))
		return
	}
	if !e.apply() {
		return
	}
	b, err := e.buildOutput()
	if err != nil {
		e.fail(err)
		return
	}
	if !saveAs && e.state.Kind == "slot" && snapshot(b).Platform != "pc" {
		e.navigate("review")
		e.fail(fmt.Errorf("use Save as… for Switch output, or select PC conversion"))
		return
	}
	if saveAs {
		e.writeDialog(b, e.state.Name, []mygo.FileFilter{{Name: "RF4S saves", Extensions: []string{"sav"}}}, func(path string) {
			e.fail(e.core.Call("markExported", nil, nil))
			e.fail(e.refresh(false))
			e.status = "Saved copy: " + path
		})
		return
	}
	e.confirm("Close the game first. Export to the selected game save? The current disk save will be backed up.", func() {
		r, err := writeGameSave(gameDirectory(), e.target, b, e.original)
		if err != nil {
			e.fail(err)
			return
		}
		e.fail(e.core.Call("markExported", nil, nil))
		e.fail(e.refresh(false))
		e.status = "Saved: " + r.Target + "\nBackup: " + r.Backup
		if len(r.CleanupErrors) > 0 {
			e.errorText = "Save written successfully. Backup cleanup warning: " + strings.Join(r.CleanupErrors, "; ")
		}
	})
}

func (e *Editor) writeDialog(data []byte, suggested string, filters []mygo.FileFilter, done func(string)) {
	original := append([]byte(nil), e.original...)
	e.dialog(func() (func(), error) {
		path, err := mygo.Dialog.Save(mygo.SaveDialogOptions{Parent: e.win, Title: e.tr("Save as…"), DefaultPath: filepath.Base(suggested), Filters: filters})
		if err != nil || path == "" {
			return nil, err
		}
		// A Save As over an existing game save must not bypass managed backups.
		if saveName.MatchString(filepath.Base(path)) && strings.EqualFold(filepath.Clean(filepath.Dir(path)), filepath.Clean(gameDirectory())) {
			s := snapshot(data)
			if !s.Valid || s.Platform == "switch" || (s.Kind == "system") != strings.EqualFold(filepath.Base(path), "rf4_sys.sav") {
				return nil, fmt.Errorf("only a valid matching PC slot or system save can replace a game-folder save")
			}
			if _, err = writeGameSave(filepath.Dir(path), filepath.Base(path), data, original); err != nil {
				return nil, err
			}
		} else if err = atomicWrite(path, data); err != nil {
			return nil, err
		}
		return func() { done(path) }, nil
	})
}
func (e *Editor) saveJSON(operation, suggested string) {
	data, err := e.core.JSON(operation, nil)
	if err != nil {
		e.fail(err)
		return
	}
	e.writeDialog([]byte(pretty(data)), suggested, []mygo.FileFilter{{Name: "JSON", Extensions: []string{"json"}}}, func(path string) { e.status = "Saved: " + path })
}

func (e *Editor) loadBackups() {
	e.backupName, e.backupSnapshot = "", Snapshot{}
	if !saveName.MatchString(e.target) {
		e.backups = nil
		return
	}
	var err error
	e.backups, err = listBackups(e.backupFolder, e.target)
	e.fail(err)
}
func (e *Editor) backupView(c *ui.Context) {
	e.note(c, "Keeps the newest 10 editor backups per save after successful export or rollback. Only matching editor .bak files are trimmed; manual copies and other saves are untouched.")
	e.card(c, "Backups & rollback", func() {
		target := e.target
		if e.choose(c, "Target save file", &target, targetChoices(), false).FillWidth().Changed() {
			e.target = target
			e.loadBackups()
		}
		ui.Text(c, e.tr("Backup folder")).FontSize(13)
		ui.TextInput(c, &e.backupFolder).Label("Backup folder").FillWidth()
		ui.Button(c, e.tr("Refresh backups")).OnClick(e.loadBackups)
		options := []Choice{}
		for _, b := range e.backups {
			options = append(options, Choice{fmt.Sprintf("%s · %d bytes", b.Name, b.Size), b.Name})
		}
		name := e.backupName
		if e.choose(c, "Backup", &name, options, false).FillWidth().Changed() {
			_, s, err := inspectBackup(e.backupFolder, e.target, name)
			if err != nil {
				e.fail(err)
			} else {
				e.backupName, e.backupSnapshot = name, s
			}
		}
		if len(options) == 0 {
			e.note(c, "No editor backups for this save.")
		}
		if e.backupName != "" {
			s := e.backupSnapshot
			e.note(c, fmt.Sprintf("%s · %s · %d bytes · CRC valid: %t\n%s", s.Kind, s.Platform, s.Size, s.Valid, s.Detail))
			ui.Button(c, e.tr("Restore selected backup on disk")).Disabled(!s.Valid || s.Platform == "switch" || e.demo).OnClick(func() {
				e.confirm("Close the game first. Restore this backup to the selected disk save? The current disk save will be backed up. Unsaved editor changes and drafts will be discarded only after a successful restore.", func() {
					r, b, err := restoreBackup(e.backupFolder, e.target, e.backupName, e.backupSnapshot.Digest)
					if err != nil {
						e.fail(err)
						return
					}
					e.fail(e.openBytes(b, r.Target, false))
					e.status = "Backup restored. Previous disk save: " + r.Backup
					if len(r.CleanupErrors) > 0 {
						e.errorText = "Backup cleanup warning: " + strings.Join(r.CleanupErrors, "; ")
					}
				})
			})
		}
	})
	e.note(c, "A valid checksum does not guarantee gameplay compatibility.")
}

func (e *Editor) loadGear() {
	err := e.core.Call("gearPreview", map[string]any{"id": e.gearID, "language": e.prefs.Names}, &e.gearPreview)
	if err != nil {
		e.gearPreview = err.Error()
	}
}
func (e *Editor) gearView(c *ui.Context) {
	e.note(c, "Adds six level-10 items to empty slots across all 60 saved bag slots. Existing items, worn gear and bag capacity are preserved. Equip them in-game after exporting.")
	e.card(c, "Equipment shortcuts", func() {
		if e.choose(c, "Equipment preset", &e.gearID, []Choice{{"Balanced optimized staff gear", "staff-balanced"}, {"Maximum-damage optimized staff gear", "staff-damage"}}, false).FillWidth().Changed() {
			e.gearRisk = false
			e.loadGear()
		}
		text := e.gearPreview
		ui.TextArea(c, &text).ReadOnly(true).Height(280).Label("Equipment preset preview")
		e.note(c, "Damage preset: Strange Pendant ignores enemy DEF/M.DEF AND your own DEF/M.DEF. It sacrifices protection. Final stats, inheritance and staff charge attacks are not simulated; test exported copies in-game.")
		ui.Checkbox(c, &e.gearRisk, e.tr("I understand experimental gear and the damage preset defense tradeoff"))
		ui.PrimaryButton(c, e.tr("Give selected staff gear")).Disabled(e.state == nil || e.state.Kind != "slot" || !e.gearRisk).OnClick(func() {
			if !e.apply() {
				return
			}
			e.fail(e.core.Call("setGearPreset", map[string]any{"id": e.gearID, "acknowledgeRisk": e.gearRisk}, nil))
			e.gearRisk = false
			e.fail(e.refresh(false))
		})
	})
}
func (e *Editor) referenceView(c *ui.Context) {
	e.note(c, "Game definitions are not saved instance stats. This does not edit game files.")
	ui.Row(c).Gap(8).Children(func() {
		ui.TextInput(c, &e.referenceID).Label("Item ID").Grow(1)
		ui.Button(c, e.tr("Look up definitions")).OnClick(func() {
			n, err := strconv.ParseInt(e.referenceID, 0, 64)
			if err != nil {
				e.fail(err)
				return
			}
			b, err := e.core.JSON("reference", map[string]any{"id": n})
			e.fail(err)
			if err == nil {
				e.referenceText = pretty(b)
			}
		})
	})
	text := e.referenceText
	ui.TextArea(c, &text).ReadOnly(true).Height(430).Label("Item definitions")
}

func (e *Editor) importTables(operation string) {
	if !e.apply() {
		return
	}
	e.dialog(func() (func(), error) {
		extensions := []string{"bin"}
		if operation == "importLanguages" {
			extensions = []string{"eng", "jpn", "fra", "deu", "kor", "twn", "chn"}
		}
		paths, err := mygo.Dialog.Open(mygo.OpenDialogOptions{Parent: e.win, Title: e.tr("Read extracted definition tables"), Multiple: operation != "importSymbols", Filters: []mygo.FileFilter{{Name: "Game tables", Extensions: extensions}}})
		if err != nil || len(paths) == 0 {
			return nil, err
		}
		limit := 21
		if operation == "importItems" {
			limit = 4
		}
		if operation == "importLanguages" {
			limit = 28
		}
		if len(paths) > limit {
			return nil, fmt.Errorf("too many reference tables")
		}
		files := []map[string]any{}
		for _, path := range paths {
			b, err := readBounded(path, 16*1024*1024)
			if err != nil {
				return nil, err
			}
			files = append(files, map[string]any{"name": filepath.Base(path), "bytes": integers(b)})
		}
		return func() {
			args := map[string]any{"files": files}
			if operation == "importSymbols" {
				args = map[string]any{"bytes": files[0]["bytes"]}
			}
			if err := e.core.Call(operation, args, nil); err != nil {
				e.fail(err)
				return
			}
			e.fail(e.core.Call("languages", nil, &e.languages))
			e.fail(e.refresh(false))
		}, nil
	})
}
func (e *Editor) importProfile() {
	if !e.apply() {
		return
	}
	e.dialog(func() (func(), error) {
		paths, err := mygo.Dialog.Open(mygo.OpenDialogOptions{Parent: e.win, Title: e.tr("Read progress profile"), Filters: []mygo.FileFilter{{Name: "Progress profile", Extensions: []string{"json"}}}})
		if err != nil || len(paths) == 0 {
			return nil, err
		}
		b, err := readBounded(paths[0], 1024*1024)
		if err != nil {
			return nil, err
		}
		var profile struct {
			Format string
			Flags  map[string]any
		}
		if err := json.Unmarshal(b, &profile); err != nil {
			return nil, err
		}
		if profile.Format != "rf4s-progress-v1" || profile.Flags == nil {
			return nil, fmt.Errorf("invalid progress profile")
		}
		return func() {
			if target, ok := profile.Flags["REG_MAIN_SCENARIO"]; ok {
				if err := e.core.Call("storyJumpPreview", map[string]any{"target": target, "flags": profile.Flags}, nil); err != nil {
					e.fail(err)
					return
				}
				e.navigate("story")
				text, _ := json.Marshal(profile.Flags)
				e.inputs["target"].Text = valueText(target)
				e.inputs["flags"].Text = string(text)
			} else {
				e.confirm("Apply progression flags? Events and world state will not be simulated.", func() {
					e.fail(e.core.Call("applyProfile", map[string]any{"text": string(b)}, nil))
					e.fail(e.refresh(false))
				})
			}
		}, nil
	})
}
