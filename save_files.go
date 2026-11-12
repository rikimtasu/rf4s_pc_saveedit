package main

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

var saveName = regexp.MustCompile(`(?i)^(rf4_s[0-9]{2}|rf4_sys)\.sav$`)

func gameDirectory() string {
	base := os.Getenv("APPDATA")
	if base == "" {
		home, _ := os.UserHomeDir()
		base = filepath.Join(home, "AppData", "Roaming")
	}
	return filepath.Join(base, "Rune Factory 4 Special")
}

func readBounded(path string, limit int64) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	b, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(b)) > limit {
		return nil, fmt.Errorf("file exceeds %d bytes", limit)
	}
	return b, nil
}

func regularDestination(path string) error {
	info, err := os.Lstat(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("refusing a linked or non-file destination: %s", path)
	}
	return nil
}

// atomicWrite never falls back to truncating the destination in place.
func atomicWrite(path string, data []byte) error {
	if err := regularDestination(path); err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".rf4s-*.tmp")
	if err != nil {
		return err
	}
	tmp := f.Name()
	defer os.Remove(tmp)
	n, err := f.Write(data)
	if err == nil && n != len(data) {
		err = io.ErrShortWrite
	}
	if err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		return err
	}
	if err = regularDestination(path); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

type Backup struct {
	Name string
	Size int64
}
type WriteResult struct {
	Target, Backup string
	CleanupErrors  []string
}

func backupPattern(filename string) *regexp.Regexp {
	return regexp.MustCompile(`(?i)^` + regexp.QuoteMeta(filename) + `\.backup-([0-9]{8}-[0-9]{6}-[0-9]{6})-([0-9]+)\.bak$`)
}

func listBackups(folder, filename string) ([]Backup, error) {
	if !saveName.MatchString(filename) {
		return nil, fmt.Errorf("choose a target save slot first")
	}
	entries, err := os.ReadDir(folder)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	pattern := backupPattern(filename)
	var records []Backup
	for _, entry := range entries {
		match := pattern.FindStringSubmatch(entry.Name())
		if match == nil {
			continue
		}
		if _, err := time.Parse("20060102-150405", match[1][:15]); err != nil {
			continue
		}
		info, err := os.Lstat(filepath.Join(folder, entry.Name()))
		if err == nil && info.Mode().IsRegular() {
			records = append(records, Backup{entry.Name(), info.Size()})
		}
	}
	sort.Slice(records, func(i, j int) bool { return strings.ToLower(records[i].Name) > strings.ToLower(records[j].Name) })
	return records, nil
}

func writeGameSave(folder, filename string, data, original []byte) (WriteResult, error) {
	var result WriteResult
	if !saveName.MatchString(filename) {
		return result, fmt.Errorf("choose a target save slot first")
	}
	filename = strings.ToLower(filename)
	if err := os.MkdirAll(folder, 0700); err != nil {
		return result, err
	}
	result.Target = filepath.Join(folder, filename)
	if err := regularDestination(result.Target); err != nil {
		return result, err
	}
	previous, err := readBounded(result.Target, 140424)
	if os.IsNotExist(err) {
		previous = original
	} else if err != nil {
		return result, err
	}
	now := time.Now()
	stamp := now.Format("20060102-150405-") + fmt.Sprintf("%06d", now.Nanosecond()/1000)
	for n := 0; n < 100; n++ {
		path := filepath.Join(folder, fmt.Sprintf("%s.backup-%s-%d.bak", filename, stamp, n))
		f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if os.IsExist(err) {
			continue
		}
		if err != nil {
			return result, err
		}
		written, err := f.Write(previous)
		if err == nil && written != len(previous) {
			err = io.ErrShortWrite
		}
		if err == nil {
			err = f.Sync()
		}
		closeErr := f.Close()
		if err == nil {
			err = closeErr
		}
		if err != nil {
			return result, err
		}
		result.Backup = path
		break
	}
	if result.Backup == "" {
		return result, fmt.Errorf("could not create a unique backup")
	}
	if err := atomicWrite(result.Target, data); err != nil {
		return result, err
	}
	// A cleanup failure is a warning after success, never a failed export.
	records, err := listBackups(folder, filename)
	if err != nil {
		result.CleanupErrors = append(result.CleanupErrors, err.Error())
		return result, nil
	}
	keep := map[string]bool{filepath.Base(result.Backup): true}
	for _, r := range records {
		if len(keep) < 10 {
			keep[r.Name] = true
		}
	}
	for _, r := range records {
		if keep[r.Name] {
			continue
		}
		path := filepath.Join(folder, r.Name)
		if err := regularDestination(path); err != nil {
			continue
		}
		if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
			result.CleanupErrors = append(result.CleanupErrors, err.Error())
		}
	}
	return result, nil
}

type Snapshot struct {
	Size                   int
	Kind, Platform, Detail string
	Valid                  bool
	Digest                 string
}

func snapshot(b []byte) Snapshot {
	s := Snapshot{Size: len(b), Kind: "unknown", Platform: "unknown", Digest: fmt.Sprintf("%x", sha256.Sum256(b))}
	get := func(n int) uint32 { return binary.LittleEndian.Uint32(b[n:]) }
	switch {
	case len(b) == 9304 && string(b[:4]) == "RF4D":
		s.Kind, s.Platform = "system", "shared"
		s.Valid = get(4) == crc32.ChecksumIEEE(b[8:])
		s.Detail = fmt.Sprintf("System flags: 0x%08X", get(16))
	case len(b) == 140424 || len(b) == 140416:
		s.Kind, s.Platform = "slot", "pc"
		if len(b) == 140416 {
			s.Platform = "switch"
		}
		s.Valid = get(0) == crc32.ChecksumIEEE(b[4:len(b)-224])
		s.Detail = fmt.Sprintf("Year %d · season %d · day %d\nMoney: %d · Order points: %d · Tourists: %d", get(0x1c), get(0x18), get(0x14), int32(get(0x4c)), int32(get(0x20710)), int32(get(0x20714)))
	}
	return s
}

func inspectBackup(folder, filename, name string) ([]byte, Snapshot, error) {
	if !saveName.MatchString(filename) || !backupPattern(filename).MatchString(name) {
		return nil, Snapshot{}, fmt.Errorf("choose a backup belonging to the selected save")
	}
	path := filepath.Join(folder, name)
	info, err := os.Lstat(path)
	if err != nil {
		return nil, Snapshot{}, err
	}
	if !info.Mode().IsRegular() {
		return nil, Snapshot{}, fmt.Errorf("refusing a linked or non-file backup")
	}
	b, err := readBounded(path, 140424)
	if err != nil {
		return nil, Snapshot{}, err
	}
	return b, snapshot(b), nil
}

func restoreBackup(folder, filename, name, digest string) (WriteResult, []byte, error) {
	b, s, err := inspectBackup(folder, filename, name)
	if err != nil {
		return WriteResult{}, nil, err
	}
	if s.Digest != digest {
		return WriteResult{}, nil, fmt.Errorf("the backup changed since the preview; review it again")
	}
	if !s.Valid || s.Platform == "switch" || (s.Kind == "system") != strings.EqualFold(filename, "rf4_sys.sav") {
		return WriteResult{}, nil, fmt.Errorf("direct rollback requires a valid matching PC slot or system-save backup")
	}
	r, err := writeGameSave(folder, filename, b, b)
	return r, b, err
}
