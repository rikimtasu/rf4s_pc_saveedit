# Named BGM / morning calls and backup rollback

These native features ship in **v0.41** and remain offline. Close RF4S before exporting or restoring saves, and keep an independent backup of your full save folder. No game files are changed.

## BGM names

**Extra orders → Other saved orders → BGM selection** now offers:

| Stored value | Selection |
| ---: | --- |
| 0 | Rune Factory 4 |
| 1 | Rune Factory 1 |
| 2 | Rune Factory 2 |
| 3 | Rune Factory 3 |
| 4 | Rune Factory Frontier |
| 5 | Rune Factory: Tides of Destiny |

The remaining four-bit values have no established menu names. An unknown loaded value remains visible and is preserved unless deliberately changed; it is not silently relabelled as a known soundtrack.

**Evidence:** the supplied PC executable's order jump table at RVA `0x1EAFC8` routes order IDs **58–63** to `0x1EA934`, which writes `REG_BGM_TYPE` using value `order_id - 58`. English `rf3mc.eng` TEXT entries **96682–96687** identify the six titles in that order. These are soundtrack-family choices, not a fabricated per-track song list.

## NPC-specific morning calls

The two controls are deliberately separate:

- **Morning-call menu unlocked (global)** edits the existing developer flag `FLG_MORNING_CALL_ORDER`.
- **Morning-call NPC** edits the selected caller: Cancel, Vishnal, Clorica, Volkanon, Bado, Lin Fa, Illuminata, Jones, Nancy or Pico. NPC labels use Game names where available, with English/Chinese fallback for Pico.

The caller is a **32-bit saved ID at `0x20728`**, not a five-bit spouse register, dating flag or a set of invented per-NPC unlock bits. Pico's ID **309** fits this field. Choosing a caller does not automatically unlock the menu or simulate wake-up dialogue/events. Cancel writes 0; friendship, romance, other NPCs and neighboring order fields are preserved. Unknown loaded IDs are not guessed.

**Evidence:** order IDs **70–79** route to `0x1EA7D2..0x1EA855` and write IDs `1,2,3,6,12,14,18,19,309,0` to runtime `0xE9AC20`. Serializer `0x7EACC/0x7EAE1` copies the containing 16-byte runtime block (`0xE9AC18`) to save `0x20720`; its `+8` member is therefore save `0x20728`. English TEXT entries **96694–96703** give the corresponding nine caller names and Cancel. This was inert inspection of the supplied executable and Bundle tables, not an in-game acceptance test.

## Ten-backup retention

After each **successful direct export or rollback**, the editor keeps at most **10 of its own backups per canonical save filename** in `%APPDATA%\Rune Factory 4 Special`.

- It backs up the **current disk bytes** before replacing the save. If the target does not exist, the supplied original/restored bytes provide the backup.
- Only regular files with the exact same-save pattern `rf4_sNN.sav.backup-YYYYMMDD-HHMMSS-microseconds-N.bak` (or the equivalent system filename) are eligible for trimming.
- Manual copies, unrelated `.bak` files, other save slots, directories and symbolic links are untouched. Save as copies are not part of this managed retention policy.
- The new pre-write backup is always retained, even if the system clock moved backwards.
- Pruning happens **after** the atomic save write succeeds. A failed write keeps the original disk file and its recovery backup. Failed writes or deletion-permission errors can temporarily leave more than 10 files; successful writes with cleanup failures show a warning rather than falsely reporting that saving failed.

This limit applies separately to each save slot and `rf4_sys.sav`, not to ten backups shared between all slots.

## Restore directly in the editor

Open **Backups & rollback**, choose the target save and select a backup. The page is available even without a loaded save.

The list shows backup time, filename and size. The preview adds format, CRC status, SHA-256 and, for slot saves, in-game date, Lest/Frey, money, order points and tourists. System saves show their saved unlock word instead. Backup time is the local timestamp embedded by the backup writer, not an invented game-save time.

Click **Restore selected backup on disk** and read the confirmation. This:

1. Rechecks that the selected same-save backup still matches the preview's hash and has a valid CRC/container.
2. Backs up the current disk save and atomically restores the selected bytes **without checksum repair or conversion**.
3. Reloads the restored save into the editor and clears the previous in-memory undo history/drafts **only after a successful restore**.

Cancel or a failed restore leaves editor changes/drafts and disk bytes untouched. The just-created backup can be used to return to the pre-rollback disk version. A corrupt, mismatched, linked or unsupported backup is refused. Direct PC-folder rollback accepts PC slot or system saves, not extracted Switch slots.

**A valid checksum does not guarantee gameplay compatibility.** Rollback does not manage Steam Cloud conflicts or restore unrelated slots/system files automatically.

## Verification scope

Focused Python checks cover retention, byte-exact restore, preservation of the current disk save, malformed/mismatched/changed backups, cleanup failures, native confirmation/cancel behavior and the named BGM/NPC controls. Per the user's request, no extra JavaScript tests or EXE smoke tests are run for this update.
