package main

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/egoist/mygo"
	"github.com/egoist/mygo/ui"
)

type Choice struct {
	Label string `json:"label"`
	Value any    `json:"value"`
}
type NavPage struct{ ID, Title, Group string }
type Field struct {
	Key, Label, Kind, OptionsRef string
	Options                      []Choice
	Optional                     bool
	Min, Max                     *float64
}
type Selector struct {
	Key, Label string
	Options    []Choice
	Value      any
}
type Tile struct {
	Slot, ID, Quantity, Level int
	Name, Icon                string
}
type PageData struct {
	Fields     []Field
	Values     map[string]any
	Records    []Choice
	Record     string
	Selectors  []Selector
	Tiles      []Tile
	Note, Info string
	Ready      bool
	OptionSets map[string][]Choice
}
type SaveState struct {
	Name, Kind, Platform, ExportState, Gender string
	Size, ChangedBytes, Undo, Redo            int
	CRCValid, Dirty                           bool
	Calendar                                  map[string]any
}
type Input struct {
	Text, Base           string
	Checked, BaseChecked bool
}
type Preferences struct{ Interface, Names string }

type Editor struct {
	core                                     *Core
	win                                      *mygo.Window
	theme                                    *ui.Theme
	nav                                      []NavPage
	page                                     string
	data                                     PageData
	context                                  map[string]any
	inputs                                   map[string]*Input
	state                                    *SaveState
	source                                   string
	original                                 []byte
	demo, busy                               bool
	status, errorText, search, preview       string
	showEmpty                                bool
	prefs                                    Preferences
	languages                                []Choice
	zh                                       map[string]string
	iconArchive                              *zip.Reader
	bitmaps                                  map[string]*ui.Bitmap
	target, platform, gender                 string
	resetAppearance, resetDating, conversion bool
	backupFolder, backupName                 string
	backups                                  []Backup
	backupSnapshot                           Snapshot
	gearID                                   string
	gearRisk                                 bool
	gearPreview                              string
	referenceID, referenceText               string
	choiceLabels                             map[string][]string
}

func nordTheme() *ui.Theme {
	t := *ui.DarkTheme()
	t.Background, t.Surface = ui.Hex("#2e3440"), ui.Hex("#3b4252")
	t.SurfaceHover, t.SurfacePressed, t.Border = ui.Hex("#434c5e"), ui.Hex("#4c566a"), ui.Hex("#4c566a")
	t.Text, t.TextMuted = ui.Hex("#eceff4"), ui.Hex("#b8c1d1")
	t.Accent, t.AccentHover, t.AccentPressed, t.AccentText = ui.Hex("#88c0d0"), ui.Hex("#8fbcbb"), ui.Hex("#81a1c1"), t.Background
	t.Focus, t.Selection, t.InactiveAccent = t.Accent, ui.Hex("#434c5e"), t.Accent
	t.Danger, t.Warning, t.Success = ui.Hex("#bf616a"), ui.Hex("#ebcb8b"), ui.Hex("#a3be8c")
	t.Inverse, t.InverseText, t.Scrollbar = t.Surface, t.Text, t.Border
	t.Radius, t.Spacing, t.FontSize, t.Font = 6, 4, 15, "Noto Sans, Noto Sans CJK SC"
	return &t
}

func newEditor(core *Core) (*Editor, error) {
	e := &Editor{core: core, theme: nordTheme(), page: "overview", context: map[string]any{}, inputs: map[string]*Input{},
		showEmpty: true, bitmaps: map[string]*ui.Bitmap{}, zh: map[string]string{},
		prefs: Preferences{Interface: "Follow system", Names: "en"}, platform: "keep", gender: "keep",
		backupFolder: gameDirectory(), gearID: "staff-balanced", referenceID: "1"}
	if err := core.Call("navigation", nil, &e.nav); err != nil {
		return nil, err
	}
	if err := core.Call("languages", nil, &e.languages); err != nil {
		return nil, err
	}
	if b, err := asset("zh.json"); err == nil {
		_ = json.Unmarshal(b, &e.zh)
	}
	if b, err := os.ReadFile(preferencePath()); err == nil {
		_ = json.Unmarshal(b, &e.prefs)
	}
	if e.prefs.Interface != "English" && e.prefs.Interface != "简体中文" {
		e.prefs.Interface = "Follow system"
	}
	if !hasChoice(e.languages, e.prefs.Names) {
		e.prefs.Names = "en"
	}
	if b, err := asset("icons.zip"); err == nil {
		e.iconArchive, _ = zip.NewReader(bytes.NewReader(b), int64(len(b)))
	}
	return e, e.refresh(false)
}

func preferencePath() string {
	dir, _ := os.UserConfigDir()
	return filepath.Join(dir, "RF4S Save Editor", "mygo.json")
}
func (e *Editor) savePreferences() {
	b, _ := json.Marshal(e.prefs)
	path := preferencePath()
	if err := os.MkdirAll(filepath.Dir(path), 0700); err == nil {
		if err = atomicWrite(path, b); err != nil {
			e.fail(err)
		}
	} else {
		e.fail(err)
	}
}
func (e *Editor) chinese() bool {
	if e.prefs.Interface != "Follow system" {
		return e.prefs.Interface == "简体中文"
	}
	return strings.HasPrefix(strings.ToLower(mygo.App.Locale()), "zh")
}
func (e *Editor) tr(s string) string {
	if e.chinese() {
		if t := e.zh[s]; t != "" {
			return t
		}
	}
	return s
}
func valueText(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprint(v)
}
func hasChoice(options []Choice, v string) bool {
	for _, o := range options {
		if valueText(o.Value) == v {
			return true
		}
	}
	return false
}

func (e *Editor) fail(err error) {
	if err != nil {
		e.errorText = err.Error()
	}
}
func (e *Editor) args() map[string]any {
	a := map[string]any{"page": e.page, "language": e.prefs.Names}
	for k, v := range e.context {
		a[k] = v
	}
	return a
}
func (e *Editor) refresh(preserve bool) error {
	if err := e.core.Call("state", nil, &e.state); err != nil {
		return err
	}
	var data PageData
	if err := e.core.Call("page", e.args(), &data); err != nil {
		return err
	}
	for i := range data.Fields {
		f := &data.Fields[i]
		if f.OptionsRef != "" {
			f.Options = data.OptionSets[f.OptionsRef]
		}
	}
	e.choiceLabels = map[string][]string{}
	e.data = data
	e.context["record"] = data.Record
	for _, s := range data.Selectors {
		e.context[s.Key] = s.Value
	}
	old := e.inputs
	e.inputs = map[string]*Input{}
	for _, f := range data.Fields {
		v := data.Values[f.Key]
		b := v == true || v == float64(1)
		in := &Input{Text: valueText(v), Base: valueText(v), Checked: b, BaseChecked: b}
		if preserve && old[f.Key] != nil {
			in = old[f.Key]
		}
		e.inputs[f.Key] = in
	}
	return nil
}
func (e *Editor) pending() bool {
	for _, f := range e.data.Fields {
		in := e.inputs[f.Key]
		if in == nil {
			continue
		}
		if f.Kind == "bool" {
			if in.Checked != in.BaseChecked {
				return true
			}
		} else if in.Text != in.Base {
			return true
		}
	}
	return false
}
func (e *Editor) unexported() bool {
	return e.pending() || e.state != nil && e.state.ExportState == "unexported"
}

func (e *Editor) formValues() (map[string]any, map[string]any, error) {
	values, changes := map[string]any{}, map[string]any{}
	for _, f := range e.data.Fields {
		in := e.inputs[f.Key]
		var v any
		changed := in.Text != in.Base
		switch f.Kind {
		case "bool":
			v, changed = in.Checked, in.Checked != in.BaseChecked
		case "text":
			v = in.Text
		case "choice":
			found := false
			for _, o := range f.Options {
				if valueText(o.Value) == in.Text {
					v, found = o.Value, true
					break
				}
			}
			if !found {
				return nil, nil, fmt.Errorf("%s: choose a listed value", f.Label)
			}
		default:
			s := strings.TrimSpace(in.Text)
			if s == "" && f.Optional {
				v = nil
				break
			}
			base := 10
			if strings.HasPrefix(strings.ToLower(s), "0x") {
				base = 0
			}
			n, err := strconv.ParseInt(s, base, 64)
			if err != nil {
				return nil, nil, fmt.Errorf("%s: enter a whole number", f.Label)
			}
			if f.Min != nil && float64(n) < *f.Min || f.Max != nil && float64(n) > *f.Max {
				return nil, nil, fmt.Errorf("%s: value is outside the allowed range", f.Label)
			}
			v = n
		}
		values[f.Key] = v
		if changed {
			changes[f.Key] = v
		}
	}
	return values, changes, nil
}

func (e *Editor) draftOperations() ([]json.RawMessage, error) {
	if !e.pending() {
		return nil, nil
	}
	v, c, err := e.formValues()
	if err != nil {
		return nil, err
	}
	a := e.args()
	a["values"], a["changes"] = v, c
	var operations []json.RawMessage
	if err := e.core.Call("operations", a, &operations); err != nil {
		return nil, err
	}
	return operations, nil
}
func (e *Editor) apply() bool {
	ops, err := e.draftOperations()
	if err != nil {
		e.fail(err)
		return false
	}
	if len(ops) == 0 {
		return true
	}
	if err := e.core.Call("applyOperations", map[string]any{"operations": ops}, nil); err != nil {
		e.fail(err)
		return false
	}
	e.errorText = ""
	e.status = e.tr("Changes applied in memory. Review and export; the original is untouched.")
	e.fail(e.refresh(false))
	return true
}
func (e *Editor) navigate(page string) {
	if page == e.page {
		return
	}
	if !e.apply() {
		return
	}
	e.page, e.context, e.search, e.preview = page, map[string]any{}, "", ""
	e.errorText = ""
	e.fail(e.refresh(false))
	if page == "gear" {
		e.loadGear()
	}
	if page == "backups" {
		e.loadBackups()
	}
}
func (e *Editor) selectContext(key string, value any) {
	if valueText(e.context[key]) == valueText(value) {
		return
	}
	if key == "witness" {
		e.context[key] = value
		if valueText(value) != "" {
			e.inputs["target"].Text = valueText(value)
		}
		return
	}
	if !e.apply() {
		return
	}
	e.context[key] = value
	if key == "container" || key == "group" {
		delete(e.context, "record")
	}
	if key == "farm" {
		delete(e.context, "patch")
	}
	e.preview = ""
	e.fail(e.refresh(false))
}
func (e *Editor) mutate(op string) {
	if e.busy || !e.apply() {
		return
	}
	if err := e.core.Call(op, nil, nil); err != nil {
		e.fail(err)
		return
	}
	e.fail(e.refresh(false))
}

func (e *Editor) openBytes(b []byte, path string, demo bool) error {
	// native-core validates before replacing the current document.
	if err := e.core.Call("open", map[string]any{"bytes": integers(b), "name": filepath.Base(path)}, nil); err != nil {
		return err
	}
	e.original, e.source, e.demo = append([]byte(nil), b...), path, demo
	e.page, e.context, e.search, e.preview, e.errorText = "overview", map[string]any{}, "", "", ""
	e.platform, e.gender, e.resetAppearance, e.resetDating, e.conversion = "keep", "keep", false, false, false
	e.target = ""
	if saveName.MatchString(filepath.Base(path)) {
		e.target = strings.ToLower(filepath.Base(path))
	}
	e.gearRisk = false
	return e.refresh(false)
}

// Dialogs block only a worker. Document/UI changes always run on MyGO's UI thread.
func (e *Editor) dialog(work func() (func(), error)) {
	if e.busy || e.win == nil {
		return
	}
	e.busy = true
	go func() {
		done, err := work()
		e.win.Update(func() {
			e.busy = false
			e.fail(err)
			if err == nil && done != nil {
				done()
			}
		})
	}()
}
func (e *Editor) confirm(message string, done func()) {
	e.dialog(func() (func(), error) {
		r, err := mygo.Dialog.Message(mygo.MessageOptions{Parent: e.win, Type: mygo.MessageWarning, Message: e.tr(message), Buttons: []string{e.tr("Cancel"), e.tr("Continue")}, DefaultButton: 0, CancelButton: 0})
		if err != nil || r.Button != 1 {
			return nil, err
		}
		return done, nil
	})
}
func (e *Editor) openDialog() {
	start := func() {
		e.dialog(func() (func(), error) {
			folder := gameDirectory()
			if e.source != "" {
				folder = filepath.Dir(e.source)
			}
			if _, err := os.Stat(folder); err != nil {
				folder, _ = os.UserHomeDir()
			}
			paths, err := mygo.Dialog.Open(mygo.OpenDialogOptions{Parent: e.win, Title: e.tr("Open a slot or system save"), DefaultPath: folder, Filters: []mygo.FileFilter{{Name: "RF4S saves", Extensions: []string{"sav"}}}})
			if err != nil || len(paths) == 0 {
				return nil, err
			}
			b, err := readBounded(paths[0], 140424)
			if err != nil {
				return nil, err
			}
			return func() { e.fail(e.openBytes(b, paths[0], false)) }, nil
		})
	}
	if e.unexported() {
		e.confirm("Discard unexported edits and drafts?", start)
	} else {
		start()
	}
}
func (e *Editor) loadDemo() {
	load := func() {
		b, err := e.core.Bytes("demoBytes", nil)
		if err == nil {
			err = e.openBytes(b, "Synthetic demo.sav", true)
		}
		e.fail(err)
	}
	if e.unexported() {
		e.confirm("Discard unexported edits and drafts?", load)
	} else {
		load()
	}
}

func (e *Editor) bitmap(name string) *ui.Bitmap {
	if name == "" || e.iconArchive == nil {
		return nil
	}
	if b, ok := e.bitmaps[name]; ok {
		return b
	}
	f, err := e.iconArchive.Open(name)
	if err != nil {
		return nil
	}
	defer f.Close()
	b, err := io.ReadAll(f)
	if err != nil {
		return nil
	}
	image, _ := ui.DecodeBitmap(b)
	e.bitmaps[name] = image
	return image
}
