package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/egoist/mygo/ui"
)

func testEditor(t *testing.T) *Editor {
	t.Helper()
	t.Setenv("APPDATA", t.TempDir())
	c, err := newCore()
	if err != nil {
		t.Fatal(err)
	}
	e, err := newEditor(c)
	if err != nil {
		t.Fatal(err)
	}
	e.prefs.Interface, e.prefs.Names = "English", "en"
	b, err := c.Bytes("demoBytes", nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := e.openBytes(b, "rf4_s00.sav", false); err != nil {
		t.Fatal(err)
	}
	return e
}
func playerMoney(t *testing.T, e *Editor) int {
	t.Helper()
	var p struct{ Money int }
	if err := e.core.Call("player", nil, &p); err != nil {
		t.Fatal(err)
	}
	return p.Money
}

func TestDraftsAndRoundTrip(t *testing.T) {
	e := testEditor(t)
	before := playerMoney(t, e)
	e.navigate("player")
	e.inputs["money"].Text = "123456"
	e.navigate("calendar")
	if e.page != "calendar" || playerMoney(t, e) != 123456 || e.state.Undo != 1 {
		t.Fatalf("draft not applied: %+v", e.state)
	}
	e.mutate("undo")
	if playerMoney(t, e) != before {
		t.Fatal("undo did not restore money")
	}
	e.mutate("redo")
	if playerMoney(t, e) != 123456 {
		t.Fatal("redo did not restore money")
	}
	b, err := e.buildOutput()
	if err != nil {
		t.Fatal(err)
	}
	if !snapshot(b).Valid {
		t.Fatal("export checksum invalid")
	}
	if err := e.openBytes(b, "rf4_s00.sav", false); err != nil {
		t.Fatal(err)
	}
	if playerMoney(t, e) != 123456 || e.state.ChangedBytes != 0 {
		t.Fatal("round trip changed values")
	}
}

func TestInvalidDraftBlocksNavigationAndAtomicEdits(t *testing.T) {
	e := testEditor(t)
	original, err := e.core.Bytes("working", nil)
	if err != nil {
		t.Fatal(err)
	}
	e.navigate("player")
	e.inputs["money"].Text = "not a number"
	e.navigate("calendar")
	if e.page != "player" || !e.pending() || e.errorText == "" {
		t.Fatal("invalid draft was discarded")
	}
	e.inputs["money"].Text = "123"
	e.inputs["tourists"].Text = "-1"
	if e.apply() {
		t.Fatal("invalid batch accepted")
	}
	after, _ := e.core.Bytes("working", nil)
	if !bytes.Equal(original, after) {
		t.Fatal("batch partially applied")
	}
	if e.state.Undo != 0 {
		t.Fatal("failed batch added undo history")
	}
}

func TestEverySlotPageBuildsAndResizes(t *testing.T) {
	e := testEditor(t)
	for _, p := range e.nav {
		if p.ID == "player-name" || p.ID == "system" {
			continue
		}
		t.Run(p.ID, func(t *testing.T) {
			e.navigate(p.ID)
			if e.errorText != "" {
				t.Fatalf("page error: %s", e.errorText)
			}
			tt := ui.NewTester(e.view, 1180, 820)
			if !tt.HasText(p.Title) {
				t.Fatalf("heading missing: %q", tt.Texts())
			}
			tt.SetSize(640, 480)
			if !tt.HasText(p.Title) {
				t.Fatal("compact heading missing")
			}
		})
	}
}

func TestNativeControlAppliesAndKeepsInvalidInput(t *testing.T) {
	e := testEditor(t)
	e.navigate("calendar")
	tt := ui.NewTester(e.view, 1180, 820)
	input, ok := tt.AccessByRole(ui.RoleTextField, "Day")
	if !ok {
		t.Fatal("Day input missing")
	}
	tt.ClickAt(input.Bounds.X+input.Bounds.W/2, input.Bounds.Y+input.Bounds.H/2)
	tt.Key(ui.Ctrl, ui.KeyA)
	tt.Type("25")
	if err := tt.Click("Apply changes"); err != nil {
		t.Fatal(err)
	}
	if e.state.Calendar["day"] != float64(25) || e.state.Undo != 1 {
		t.Fatalf("native form failed: %+v, error %s", e.state, e.errorText)
	}
	input, _ = tt.AccessByRole(ui.RoleTextField, "Day")
	tt.ClickAt(input.Bounds.X+input.Bounds.W/2, input.Bounds.Y+input.Bounds.H/2)
	tt.Key(ui.Ctrl, ui.KeyA)
	tt.Type("31")
	if err := tt.Click("Player values"); err != nil {
		t.Fatal(err)
	}
	if e.page != "calendar" || e.inputs["day"].Text != "31" {
		t.Fatal("invalid native draft lost")
	}
}

func TestNamesAndLanguagePreserveDraft(t *testing.T) {
	e := testEditor(t)
	e.navigate("inventory")
	e.inputs["quantity"].Text = "7"
	e.prefs.Names = "zh-Hans"
	if err := e.refresh(true); err != nil {
		t.Fatal(err)
	}
	if e.inputs["quantity"].Text != "7" || !e.pending() {
		t.Fatal("language switch lost draft")
	}
	if e.state.Undo != 0 {
		t.Fatal("language switch edited save")
	}
}

func TestInventoryReplacementAndRawZero(t *testing.T) {
	e := testEditor(t)
	e.navigate("inventory")
	// The first demo slot has an item. Clearing it uses the native validator.
	e.inputs["id"].Text = "0"
	e.adjustQuantity()
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	var item struct{ ID, Quantity int }
	if err := e.core.Call("item", map[string]any{"container": "bag", "slot": 0}, &item); err != nil {
		t.Fatal(err)
	}
	if item.ID != 0 || item.Quantity != 0 {
		t.Fatalf("not cleared: %+v", item)
	}
	e.navigate("raw")
	e.inputs["offset"].Text = "0x4c"
	e.inputs["value"].Text = "0"
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	if playerMoney(t, e) != 0 {
		t.Fatal("raw zero not written")
	}
}

func TestSystemUnlockAndPlayerNames(t *testing.T) {
	e := testEditor(t)
	b := make([]byte, 9304)
	copy(b, "RF4D")
	binary.LittleEndian.PutUint32(b[4:], crc32.ChecksumIEEE(b[8:]))
	if err := e.openBytes(b, "rf4_sys.sav", false); err != nil {
		t.Fatal(err)
	}
	e.navigate("system")
	e.inputs["0"].Checked = true
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	out, err := e.buildOutput()
	if err != nil {
		t.Fatal(err)
	}
	if binary.LittleEndian.Uint32(out[16:])&1 == 0 || !snapshot(out).Valid {
		t.Fatal("system unlock did not round trip")
	}
	e.navigate("player-name")
	tt := ui.NewTester(e.view, 640, 480)
	if !tt.HasText("Player name") || e.data.Ready {
		t.Fatal("empty name record editable")
	}
}

func TestDemoAndConversionGuards(t *testing.T) {
	e := testEditor(t)
	e.demo = true
	if _, err := e.buildOutput(); err == nil {
		t.Fatal("demo exported")
	}
	e.demo, e.platform = false, "switch"
	if _, err := e.buildOutput(); err == nil {
		t.Fatal("conversion without consent")
	}
	e.conversion = true
	b, err := e.buildOutput()
	if err != nil {
		t.Fatal(err)
	}
	if len(b) != 140416 || !snapshot(b).Valid {
		t.Fatal("bad Switch output")
	}
}

func TestBackupRetentionAndRestore(t *testing.T) {
	e := testEditor(t)
	folder := t.TempDir()
	filename := "rf4_s00.sav"
	original, err := e.buildOutput()
	if err != nil {
		t.Fatal(err)
	}
	manual := filepath.Join(folder, "manual.bak")
	if err := os.WriteFile(manual, []byte("manual"), 0600); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 12; i++ {
		e.navigate("player")
		e.inputs["money"].Text = fmt.Sprint(5000 + i)
		if !e.apply() {
			t.Fatal(e.errorText)
		}
		b, err := e.buildOutput()
		if err != nil {
			t.Fatal(err)
		}
		r, err := writeGameSave(folder, filename, b, original)
		if err != nil {
			t.Fatal(err)
		}
		if len(r.CleanupErrors) > 0 {
			t.Fatal(r.CleanupErrors)
		}
	}
	backups, err := listBackups(folder, filename)
	if err != nil {
		t.Fatal(err)
	}
	if len(backups) != 10 {
		t.Fatalf("got %d backups", len(backups))
	}
	if _, err := os.Stat(manual); err != nil {
		t.Fatal("manual backup removed")
	}
	b, s, err := inspectBackup(folder, filename, backups[0].Name)
	if err != nil {
		t.Fatal(err)
	}
	if !s.Valid {
		t.Fatal("invalid backup")
	}
	if _, _, err := restoreBackup(folder, filename, backups[0].Name, "wrong"); err == nil {
		t.Fatal("changed preview accepted")
	}
	r, restored, err := restoreBackup(folder, filename, backups[0].Name, s.Digest)
	if err != nil {
		t.Fatal(err)
	}
	disk, _ := os.ReadFile(r.Target)
	if !bytes.Equal(b, disk) || !bytes.Equal(b, restored) {
		t.Fatal("restore not byte exact")
	}
}

func TestRejectUnsafePathsAndPreserveDestination(t *testing.T) {
	folder := t.TempDir()
	path := filepath.Join(folder, "existing.sav")
	if err := os.WriteFile(path, []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := atomicWrite(path, []byte("new")); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(path)
	if string(b) != "new" {
		t.Fatal("atomic replace failed")
	}
	if _, err := writeGameSave(folder, "../rf4_s00.sav", nil, nil); err == nil {
		t.Fatal("traversal accepted")
	}
	if _, _, err := inspectBackup(folder, "rf4_s00.sav", "../other"); err == nil {
		t.Fatal("backup traversal accepted")
	}
	if err := os.Mkdir(filepath.Join(folder, "rf4_s00.sav"), 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := writeGameSave(folder, "rf4_s00.sav", nil, nil); err == nil || !strings.Contains(err.Error(), "non-file") {
		t.Fatal("directory destination accepted", err)
	}
}

func TestSavedCheckboxesAreIntegersButConsentStaysBoolean(t *testing.T) {
	e := testEditor(t)
	for _, test := range []struct{ page, key string }{{"orders", "noExp"}, {"relationships", "dating"}, {"marriage", "marriageEvent"}, {"soil", "yieldNegative"}} {
		t.Run(test.page, func(t *testing.T) {
			e.navigate(test.page)
			in := e.inputs[test.key]
			if in == nil {
				t.Fatalf("missing %s", test.key)
			}
			in.Checked = !in.Checked
			if !e.apply() {
				t.Fatal(e.errorText)
			}
			if e.inputs[test.key].Checked != in.Checked {
				t.Fatal("checkbox did not round trip")
			}
		})
	}
	// A story jump still needs a true boolean acknowledgement, not a saved bit.
	e.navigate("story")
	e.inputs["target"].Text = "511"
	if e.apply() {
		t.Fatal("story jump accepted without consent")
	}
	e.inputs["acknowledgeRisk"].Checked = true
	if !e.apply() {
		t.Fatal(e.errorText)
	}
}

func TestRosterAndMonsterStatsThroughForms(t *testing.T) {
	e := testEditor(t)
	if err := e.core.Call("setFlag", map[string]any{"name": "REG_MON_HOUSE0_L_LV", "value": 1}, nil); err != nil {
		t.Fatal(err)
	}
	e.navigate("roster")
	if !e.data.Ready {
		t.Fatal("built barn not available")
	}
	e.inputs["name"].Text = "芙蕾A"
	e.inputs["acknowledgeRisk"].Checked = true
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	e.navigate("monsters")
	if !e.data.Ready {
		t.Fatal("created monster not shown")
	}
	e.inputs["friendship"].Text = "25"
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	var monsters []struct {
		Name       string
		Friendship int
	}
	if err := e.core.Call("monsters", nil, &monsters); err != nil {
		t.Fatal(err)
	}
	if len(monsters) != 1 || monsters[0].Name != "芙蕾A" || monsters[0].Friendship != 25 {
		t.Fatalf("bad roster %+v", monsters)
	}
}

func TestSystemNameUTF8RoundTrip(t *testing.T) {
	e := testEditor(t)
	b := make([]byte, 9304)
	copy(b, "RF4D")
	b[8] = 1
	binary.LittleEndian.PutUint32(b[4:], crc32.ChecksumIEEE(b[8:]))
	if err := e.openBytes(b, "rf4_sys.sav", false); err != nil {
		t.Fatal(err)
	}
	e.navigate("player-name")
	if !e.data.Ready {
		t.Fatal("existing name slot not editable")
	}
	e.inputs["name"].Text = "芙蕾A"
	if !e.apply() {
		t.Fatal(e.errorText)
	}
	out, err := e.buildOutput()
	if err != nil {
		t.Fatal(err)
	}
	if string(bytes.TrimRight(out[0x504:0x517], "\x00")) != "芙蕾A" || !snapshot(out).Valid {
		t.Fatal("UTF-8 name did not round trip")
	}
}

func TestMalformedUTF8IsRejected(t *testing.T) {
	e := testEditor(t)
	b := []byte{'T', 'E', 'X', 'T', 1, 0, 0, 0, 1, 0, 0, 0, 16, 0, 0, 0, 0xff, 0}
	if err := e.core.Call("importLanguages", map[string]any{"files": []map[string]any{{"name": "rf3TxtItem_split2_1.chn", "bytes": integers(b)}}}, nil); err == nil {
		t.Fatal("malformed UTF-8 imported")
	}
}
