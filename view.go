package main

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"

	"github.com/egoist/mygo/ui"
)

func (e *Editor) view(c *ui.Context) {
	c.SetTheme(e.theme)
	width, _ := c.Size()
	root := ui.Column(c).Fill().FontWeight(500).Disabled(e.busy)
	root.Children(func() {
		ui.Row(c).Grow(1).MinHeight(0).AlignItems(ui.Stretch).Children(func() {
			if width >= 860 {
				e.sidebar(c)
			}
			ui.Column(c).Grow(1).MinWidth(0).Children(func() {
				e.header(c, width < 860)
				if e.errorText != "" {
					ui.Row(c).Padding(10, 20).Gap(12).Background(e.theme.Danger.Alpha(.15)).Children(func() {
						ui.Text(c, e.errorText).Grow(1).TextColor(e.theme.Warning).Role(ui.RoleAlert)
						ui.Button(c, e.tr("Dismiss")).OnClick(func() { e.errorText = "" })
					})
				}
				if e.status != "" {
					ui.Row(c.Key("status")).Padding(8, 20).Gap(12).Children(func() {
						ui.Text(c, e.status).Grow(1).FontSize(12).TextColor(e.theme.Success).Role(ui.RoleStatus)
						ui.Button(c, e.tr("Dismiss")).OnClick(func() { e.status = "" })
					})
				}
				ui.Scroll(c.Key(e.page)).Grow(1).MinHeight(0).Padding(24).Gap(18).Children(func() {
					switch e.page {
					case "overview":
						e.overview(c)
					case "review":
						e.review(c)
					case "backups":
						e.backupView(c)
					case "gear":
						e.gearView(c)
					case "reference":
						e.referenceView(c)
					default:
						e.formPage(c, width)
					}
				})
			})
		})
		ui.Row(c).Padding(8, 16).Gap(12).Background(e.theme.Surface).Children(func() {
			ui.Text(c, e.documentStatus()).FontSize(12).TextColor(e.theme.Accent)
			ui.Spacer(c)
			if e.state != nil {
				ui.Text(c, fmt.Sprintf("%d bytes changed", e.state.ChangedBytes)).FontSize(12).TextColor(e.theme.TextMuted)
			}
			ui.Text(c, "MyGO · Nord").FontSize(12).TextColor(e.theme.TextMuted)
		})
	})
	if !e.busy {
		c.OnShortcut(ui.Ctrl, ui.KeyO, e.openDialog)
		c.OnShortcut(ui.Ctrl, ui.KeyS, func() { e.export(false) })
		c.OnShortcut(ui.Ctrl|ui.Shift, ui.KeyS, func() { e.export(true) })
		c.OnShortcut(ui.Ctrl, ui.KeyZ, func() { e.mutate("undo") })
		c.OnShortcut(ui.Ctrl, ui.KeyY, func() { e.mutate("redo") })
		c.OnShortcut(ui.Ctrl|ui.Shift, ui.KeyL, func() { e.learnRecipes(true, true) })
	}
}

func (e *Editor) documentStatus() string {
	if e.state == nil {
		return e.tr("No save loaded")
	}
	if e.demo {
		return e.tr("Demo · export disabled")
	}
	if e.pending() {
		return e.tr("Pending edit · saved on export")
	}
	switch e.state.ExportState {
	case "unexported":
		return e.tr("Unexported changes")
	case "exported":
		return e.tr("Current edits exported")
	}
	return e.tr("Original loaded · no edits")
}

func (e *Editor) sidebar(c *ui.Context) {
	ui.Column(c).Width(220).Shrink(0).Background(e.theme.Surface).Children(func() {
		ui.Column(c).Padding(24, 18).Gap(4).Children(func() {
			ui.Text(c, "Rune Factory 4").FontSize(19).TextColor(e.theme.Accent)
			ui.Text(c, "Special · Save editor").FontSize(13).TextColor(e.theme.TextMuted)
		})
		ui.Scroll(c).Grow(1).Padding(0, 10, 16, 10).Gap(2).Children(func() {
			group := ""
			for _, p := range e.nav {
				if p.Group != group {
					group = p.Group
					ui.Text(c, e.tr(group)).FontSize(11).TextColor(e.theme.TextMuted).Padding(14, 10, 5, 10)
				}
				button := ui.Button(c.Key(p.ID), e.tr(p.Title)).FillWidth().Justify(ui.Start).Padding(9, 10).NoShadow().Border(0, ui.Transparent)
				if e.page == p.ID {
					button.Background(e.theme.Accent).TextColor(e.theme.AccentText)
				} else {
					button.Background(ui.Transparent)
				}
				button.OnClick(func() { e.navigate(p.ID) })
			}
		})
		ui.Text(c, e.tr("Offline · edits stay in memory")).FontSize(11).TextColor(e.theme.TextMuted).Padding(14, 18)
	})
}

func (e *Editor) header(c *ui.Context, compact bool) {
	title := "Save overview"
	for _, p := range e.nav {
		if p.ID == e.page {
			title = p.Title
		}
	}
	ui.Column(c).Padding(16, 24).Gap(12).BorderWidth(0, 0, 1, 0).BorderColor(e.theme.Border).Children(func() {
		ui.Row(c).Wrap().Gap(8).Children(func() {
			ui.Text(c, e.tr(title)).FontSize(23).Grow(1)
			ui.Button(c, e.tr("Open save")).OnClick(e.openDialog)
			ui.Button(c, e.tr("Undo")).Disabled(e.state == nil || e.state.Undo == 0).OnClick(func() { e.mutate("undo") })
			ui.Button(c, e.tr("Redo")).Disabled(e.state == nil || e.state.Redo == 0).OnClick(func() { e.mutate("redo") })
			ui.PrimaryButton(c, e.tr("Export edited save")).Disabled(e.state == nil || e.demo).OnClick(func() { e.export(false) })
		})
		ui.Row(c).Wrap().Gap(8).Children(func() {
			if compact {
				value := e.page
				opts := make([]Choice, len(e.nav))
				for i, p := range e.nav {
					opts[i] = Choice{p.Title, p.ID}
				}
				if e.choose(c, "Section", &value, opts, false).Changed() {
					e.navigate(value)
				}
			} else {
				name := "No save loaded"
				if e.state != nil {
					name = e.state.Name
				}
				ui.Text(c, name).FontSize(13).TextColor(e.theme.TextMuted).Grow(1)
			}
			mode := e.prefs.Interface
			ui.Text(c, e.tr("Interface:")).FontSize(12).TextColor(e.theme.TextMuted)
			if e.choose(c, "Interface / 界面", &mode, []Choice{{"Follow system", "Follow system"}, {"English", "English"}, {"简体中文", "简体中文"}}, false).Changed() {
				e.prefs.Interface = mode
				e.savePreferences()
			}
			lang := e.prefs.Names
			ui.Text(c, e.tr("Game names:")).FontSize(12).TextColor(e.theme.TextMuted)
			if e.choose(c, "Game names", &lang, e.languages, false).Changed() {
				e.prefs.Names = lang
				e.savePreferences()
				e.fail(e.refresh(true))
			}
		})
	})
}

// Values and display labels are separate: localization never changes stored IDs.
func (e *Editor) choose(c *ui.Context, label string, value *string, options []Choice, search bool) ui.Element {
	cacheKey := ""
	if len(options) > 0 {
		for key, shared := range e.data.OptionSets {
			if len(shared) == len(options) && &shared[0] == &options[0] {
				cacheKey = key + "/" + e.uiLanguage()
				break
			}
		}
	}
	labels := e.choiceLabels[cacheKey]
	if cacheKey == "" || labels == nil {
		labels = make([]string, len(options))
		for i, o := range options {
			labels[i] = e.tr(o.Label)
		}
		if cacheKey != "" {
			e.choiceLabels[cacheKey] = labels
		}
	}
	selected := ""
	for i, o := range options {
		if valueText(o.Value) == *value {
			selected = labels[i]
			break
		}
	}
	var control ui.Element
	if search {
		control = ui.Combobox(c, &selected, labels).Label(e.tr(label))
	} else {
		control = ui.Select(c, &selected, labels).Label(e.tr(label))
	}
	if control.Changed() {
		for i, s := range labels {
			if s == selected {
				*value = valueText(options[i].Value)
				break
			}
		}
	}
	return control
}

func (e *Editor) card(c *ui.Context, title string, body func()) {
	ui.Column(c).Padding(20).Gap(14).Background(e.theme.Surface).Border(1, e.theme.Border).Radius(10).Children(func() {
		if title != "" {
			ui.Text(c, e.tr(title)).FontSize(17)
		}
		body()
	})
}
func (e *Editor) note(c *ui.Context, text string) {
	if text != "" {
		ui.Text(c, e.tr(text)).TextColor(e.theme.TextMuted).FontSize(13)
	}
}

func (e *Editor) overview(c *ui.Context) {
	e.card(c, "Save overview", func() {
		if e.state == nil {
			ui.Text(c, e.tr("Open a save to start editing")).FontSize(25)
			e.note(c, "Close the game and back up your save folder first. Open a PC / Steam save, an extracted Switch save, or rf4_sys.sav.")
		} else {
			ui.Text(c, e.state.Name).FontSize(25).TextColor(e.theme.Accent)
			ui.Row(c).Wrap().Gap(24).Children(func() {
				for _, v := range []struct{ label, value string }{{"Format", strings.ToUpper(e.state.Platform) + " · " + e.state.Kind}, {"Size", fmt.Sprintf("%d bytes", e.state.Size)}, {"Checksum", map[bool]string{true: "Valid", false: "Mismatch · rebuilt on export"}[e.state.CRCValid]}} {
					ui.Column(c).Gap(5).Children(func() { e.note(c, v.label); ui.Text(c, e.tr(v.value)).FontSize(17) })
				}
			})
		}
		ui.Row(c).Wrap().Gap(8).Children(func() {
			ui.PrimaryButton(c, e.tr("Open save")).OnClick(e.openDialog)
			ui.Button(c, e.tr("Try synthetic demo")).OnClick(e.loadDemo)
			ui.Button(c, e.tr("Review & export")).Disabled(e.state == nil).OnClick(func() { e.navigate("review") })
		})
	})
	e.card(c, "Edit safely", func() {
		e.note(c, "Edits stay in memory until you export. Valid drafts apply when switching records or pages. Invalid drafts stay visible and block export. Undo changes memory, not files already on disk.")
		e.note(c, "Export edited save writes to the game save folder after making a backup. Save as… writes a separate copy. A valid checksum does not guarantee gameplay compatibility.")
	})
	e.card(c, "Game references & languages", func() {
		e.note(c, "Bundled names, icons, item effects and recipes are used offline. Optional table imports do not modify game files.")
		ui.Row(c).Wrap().Gap(8).Children(func() {
			ui.Button(c, e.tr("Read extracted item tables")).OnClick(func() { e.importTables("importItems") })
			ui.Button(c, e.tr("Read extracted recipe tables")).OnClick(func() { e.importTables("importRecipes") })
			ui.Button(c, e.tr("Read extracted language names")).OnClick(func() { e.importTables("importLanguages") })
			ui.Button(c, e.tr("Read symbols")).OnClick(func() { e.importTables("importSymbols") })
		})
	})
	if e.status != "" {
		e.note(c, e.status)
	}
}

func (e *Editor) formPage(c *ui.Context, width float32) {
	e.note(c, e.data.Note)
	for _, selector := range e.data.Selectors {
		ui.Row(c.Key("selector-" + selector.Key)).Wrap().Gap(10).Children(func() {
			ui.Text(c, e.tr(selector.Label)).Width(130)
			value := valueText(e.context[selector.Key])
			control := e.choose(c, selector.Label, &value, selector.Options, len(selector.Options) > 30).Grow(1)
			if control.Changed() {
				for _, o := range selector.Options {
					if valueText(o.Value) == value {
						e.selectContext(selector.Key, o.Value)
						break
					}
				}
			}
		})
	}
	if len(e.data.Records) > 0 {
		ui.TextInput(c, &e.search).Placeholder(e.tr("Filter records by name or ID")).Label("Filter records")
		options := []Choice{}
		for _, o := range e.data.Records {
			if strings.Contains(strings.ToLower(o.Label+" "+valueText(o.Value)), strings.ToLower(e.search)) {
				options = append(options, o)
			}
		}
		value := valueText(e.context["record"])
		if e.choose(c, "Record", &value, options, true).FillWidth().Changed() {
			e.selectContext("record", value)
		}
		if len(options) == 0 {
			e.note(c, "No matching records")
		}
	}
	if e.page == "inventory" {
		e.inventoryGrid(c, width)
	}
	if e.data.Info != "" {
		e.note(c, e.data.Info)
	}
	if !e.data.Ready {
		e.note(c, "No editable records available.")
		return
	}
	e.pageTools(c)
	e.card(c, "", func() {
		columns := 1
		if width >= 1100 && len(e.data.Fields) > 6 {
			columns = 2
		}
		ui.Grid(c).Columns(columns).Gap(16).Children(func() {
			for _, f := range e.data.Fields {
				ui.Column(c.Key(f.Key)).MinWidth(0).Gap(7).Children(func() {
					in := e.inputs[f.Key]
					if f.Kind == "bool" {
						ui.Checkbox(c, &in.Checked, e.tr(f.Label)).FillWidth()
						return
					}
					ui.Text(c, e.tr(f.Label)).FontSize(13).TextColor(e.theme.TextMuted)
					if f.Kind == "choice" {
						control := e.choose(c, f.Label, &in.Text, f.Options, len(f.Options) > 20).FillWidth()
						if control.Changed() && e.page == "inventory" && f.Key == "id" {
							e.adjustQuantity()
						}
					} else {
						input := ui.TextInput(c, &in.Text).Label(e.tr(f.Label)).FillWidth()
						if f.Optional {
							input.Placeholder(e.tr("Blank keeps existing values"))
						}
					}
				})
			}
		})
		ui.Row(c).Wrap().Gap(8).Children(func() {
			label := "No draft"
			if e.pending() {
				label = "Pending edit · saved on export"
			}
			ui.Text(c, e.tr(label)).FontSize(13).TextColor(e.theme.Accent).Grow(1)
			ui.Button(c, e.tr("Clear draft")).OnClick(func() { e.fail(e.refresh(false)) })
			ui.PrimaryButton(c, e.tr("Apply changes")).Disabled(!e.pending()).OnClick(func() { e.apply() })
		})
	})
	if e.preview != "" {
		e.card(c, "Preview only", func() { text := e.preview; ui.TextArea(c, &text).ReadOnly(true).Height(230).Label("Preview") })
	}
}

func (e *Editor) inventoryGrid(c *ui.Context, width float32) {
	ui.Row(c).Wrap().Gap(10).Children(func() {
		ui.TextInput(c, &e.search).Placeholder(e.tr("Filter saved items by name or slot")).Label("Filter saved items").Grow(1)
		ui.Checkbox(c, &e.showEmpty, e.tr("Show empty slots"))
	})
	filtered := []Tile{}
	for _, t := range e.data.Tiles {
		if (e.showEmpty || t.ID != 0) && strings.Contains(strings.ToLower(fmt.Sprintf("%d %s", t.Slot+1, t.Name)), strings.ToLower(e.search)) {
			filtered = append(filtered, t)
		}
	}
	columns := int((width - 290) / 108)
	if width < 860 {
		columns = int((width - 64) / 108)
	}
	if columns < 2 {
		columns = 2
	}
	rows := (len(filtered) + columns - 1) / columns
	ui.List(c, nil, rows, func(row int) {
		ui.Row(c).Gap(8).Padding(0, 0, 8, 0).Children(func() {
			for i := row * columns; i < (row+1)*columns && i < len(filtered); i++ {
				t := filtered[i]
				box := ui.Column(c.Key(t.Slot)).Width(100).Height(108).Padding(8).Gap(4).Radius(8).Background(e.theme.Surface).Border(1, e.theme.Border).Focusable().Label(fmt.Sprintf("Saved slot %d: %s", t.Slot+1, t.Name))
				if valueText(e.context["record"]) == fmt.Sprint(t.Slot) {
					box.Border(2, e.theme.Accent)
				}
				box.Children(func() {
					ui.Row(c).Height(38).Justify(ui.Center).Children(func() {
						if b := e.bitmap(t.Icon); b != nil {
							ui.Image(c, b).Size(36, 36)
						} else {
							ui.Text(c, "·").FontSize(26).TextColor(e.theme.TextMuted)
						}
					})
					ui.Text(c, t.Name).FontSize(11).MaxLines(1)
					ui.Row(c).Children(func() {
						ui.Text(c, fmt.Sprintf("%02d", t.Slot+1)).FontSize(11).TextColor(e.theme.TextMuted)
						ui.Spacer(c)
						if t.Quantity > 0 {
							ui.Text(c, fmt.Sprintf("×%d", t.Quantity)).FontSize(11).TextColor(e.theme.Accent)
						}
					})
				})
				box.OnClick(func() { e.selectContext("record", fmt.Sprint(t.Slot)) })
			}
		})
	}).Height(236).Label("Saved item grid")
	if len(filtered) == 0 {
		e.note(c, "No matching items")
	}
}

func (e *Editor) pageTools(c *ui.Context) {
	ui.Row(c).Wrap().Gap(8).Children(func() {
		switch e.page {
		case "inventory":
			ui.Button(c, e.tr("Item effect preview")).OnClick(e.previewItem)
		case "recipes":
			ui.Button(c, e.tr("Learn all recipes")).OnClick(func() { e.learnRecipes(true, true) })
			ui.Button(c, e.tr("Learn filtered recipes")).OnClick(func() { e.learnRecipes(false, true) })
			ui.Button(c, e.tr("Forget filtered recipes")).OnClick(func() { e.learnRecipes(false, false) })
		case "relationships":
			ui.Button(c, e.tr("Reset both for current gender")).OnClick(func() {
				var r struct{ Defaults map[string]any }
				e.fail(e.core.Call("relationshipDefaults", map[string]any{"id": e.context["record"]}, &r))
				for k, v := range r.Defaults {
					if in := e.inputs[k]; in != nil {
						in.Text = valueText(v)
					}
				}
			})
		case "player-name":
			ui.Button(c, e.tr("Reset player name to game default")).OnClick(func() { e.inputs["name"].Text = "" })
		case "system":
			ui.Button(c, e.tr("Prepare extra-orders unlock")).OnClick(func() {
				if in := e.inputs["0"]; in != nil {
					in.Checked = true
				}
			})
		case "soil":
			ui.Button(c, e.tr("Prepare soil health 255")).OnClick(func() { e.inputs["health"].Text = "255" })
			ui.Button(c, e.tr("Prepare maximum soil stats (raw)")).OnClick(func() {
				var r struct{ Maximum map[string]any }
				if err := e.core.Call("soilConstants", nil, &r); err != nil {
					e.fail(err)
					return
				}
				e.stage(r.Maximum)
			})
		case "story":
			ui.Button(c, e.tr("Preview story jump")).OnClick(func() {
				v, _, err := e.formValues()
				if err == nil {
					err = e.core.Call("storyPreview", map[string]any{"values": v, "language": e.uiLanguage()}, &e.preview)
				}
				e.fail(err)
			})
			ui.Button(c, e.tr("Stage end-game flags (experimental)")).OnClick(func() {
				var r struct {
					Target any
					Flags  any
				}
				if err := e.core.Call("endgameShortcut", nil, &r); err != nil {
					e.fail(err)
					return
				}
				b, _ := json.Marshal(r.Flags)
				e.inputs["target"].Text = valueText(r.Target)
				e.inputs["flags"].Text = string(b)
			})
			ui.Button(c, e.tr("Read progress profile")).OnClick(e.importProfile)
		case "flags":
			ui.Button(c, e.tr("Evidence / edit impact")).OnClick(func() {
				v, _, err := e.formValues()
				if err == nil {
					var b json.RawMessage
					b, err = e.core.JSON("flagImpact", map[string]any{"name": e.context["record"], "value": v["value"]})
					e.preview = pretty(b)
				}
				e.fail(err)
			})
			ui.Button(c, e.tr("Download progress profile")).OnClick(func() { e.saveJSON("profile", "save.progress.json") })
			ui.Button(c, e.tr("Read progress profile")).OnClick(e.importProfile)
		case "raw":
			ui.Button(c, e.tr("Inspect current integer")).OnClick(func() {
				v, _, err := e.formValues()
				if err == nil {
					var n any
					err = e.core.Call("readNumber", v, &n)
					e.preview = valueText(n)
				}
				e.fail(err)
			})
		}
	})
}
func (e *Editor) uiLanguage() string {
	if e.chinese() {
		return "zh-CN"
	}
	return "en"
}
func (e *Editor) stage(values map[string]any) {
	for k, v := range values {
		if in := e.inputs[k]; in != nil {
			in.Text = valueText(v)
			in.Checked = v == true || v == float64(1)
		}
	}
}
func pretty(b []byte) string {
	var out strings.Builder
	var v any
	if json.Unmarshal(b, &v) == nil {
		s, _ := json.MarshalIndent(v, "", "  ")
		out.Write(s)
	}
	return out.String()
}

func (e *Editor) adjustQuantity() {
	var r struct{ Stack int }
	id, err := strconv.Atoi(e.inputs["id"].Text)
	if err != nil {
		e.fail(err)
		return
	}
	if err := e.core.Call("definition", map[string]any{"id": id}, &r); err != nil {
		e.fail(err)
		return
	}
	q := e.inputs["quantity"]
	var n int
	fmt.Sscan(q.Text, &n)
	if n < 1 {
		n = 1
	}
	if n > r.Stack {
		n = r.Stack
	}
	q.Text = fmt.Sprint(n)
}
func (e *Editor) previewItem() {
	v, changes, err := e.formValues()
	if err != nil {
		e.fail(err)
		return
	}
	a := e.args()
	a["values"], a["changes"] = v, changes
	type previewView struct {
		Item struct {
			Name      string
			ID, Level int
		}
		Sections []struct {
			Title, Name string
			Available   bool
			Effects     []struct {
				Label, Unit, Kind string
				Value             any
			}
		}
		Notices []string
	}
	var r struct {
		Before, After previewView
		Scope         string
	}
	err = e.core.Call("itemPreview", a, &r)
	if err == nil {
		lines := []string{e.tr(r.Scope)}
		for _, view := range []struct {
			title string
			value previewView
		}{{"Current item", r.Before}, {"Draft result", r.After}} {
			lines = append(lines, "", e.tr(view.title), fmt.Sprintf("%s · #%d · Lv %d", view.value.Item.Name, view.value.Item.ID, view.value.Item.Level))
			for _, section := range view.value.Sections {
				lines = append(lines, "", e.tr(section.Title)+" · "+section.Name)
				if !section.Available {
					lines = append(lines, e.tr("Read your game equipment / use / upgrade tables to preview effects."))
				}
				for _, effect := range section.Effects {
					text := e.tr(effect.Label)
					if effect.Kind != "flag" {
						text += ": " + valueText(effect.Value) + e.tr(effect.Unit)
					}
					lines = append(lines, text)
				}
			}
			for _, notice := range view.value.Notices {
				lines = append(lines, "", e.tr(notice))
			}
		}
		e.preview = strings.Join(lines, "\n")
	}
	e.fail(err)
}
func (e *Editor) learnRecipes(all, known bool) {
	if e.state == nil || e.state.Kind != "slot" {
		return
	}
	ops, err := e.draftOperations()
	if err != nil {
		e.fail(err)
		return
	}
	err = e.core.Call("learnRecipes", map[string]any{"all": all, "known": known, "group": e.context["group"], "query": e.search, "language": e.prefs.Names, "operations": ops}, nil)
	if err != nil {
		e.fail(err)
		return
	}
	e.fail(e.refresh(false))
}
