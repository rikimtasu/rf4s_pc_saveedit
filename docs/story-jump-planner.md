# Story jump planner

The **Story jump planner** is in native **Expert: story flags**. The legacy browser has a combined jump preview in **Progress profiles**. Both are available from v0.4; previous release executables are unchanged.

The planner previews and validates a stage together with explicit named flags, then applies them as one undoable edit. **It does not reconstruct a universally playable checkpoint for any act, boss or scene.** No game was launched and no exported jump was tested in-game during implementation.

## Story register and checkpoint dependencies

`REG_MAIN_SCENARIO` is a nine-bit numeric register, not a snapshot of the world. The normal game operation advances only when the new number is greater than the current number. It also updates live state and passes through an achievement-related writer path at values ≥430. An offline edit does none of that runtime work.

The packed register begins at physical bit 0 of the flag blob at `0x1E8C4`. Physical bits are addressed LSB-first within each byte, but the value's most significant bit is stored first. The editor therefore must use its packed-field writer, not write an ordinary little-endian integer. Editing the stage can change the first byte and only bit 0 of the second byte; the neighboring register stays intact.

A meaningful checkpoint can also depend on completion bits, epilogue latches, map barriers, existing NPC records and schedules, party/location, request payloads and past rewards. Copying the flag blob from a donor does not copy those other records. Neither a matching checksum nor matching a few observed flags proves playability. The primary evidence is in [the story investigation](story-flag-investigation.md).

## Using the native planner

1. Close the game and back up the **entire** save folder. Open the slot you want to edit.
2. Open **Expert: story flags → Story jump planner**. Enter a target `0–511`, or choose a script witness: a milestone observed in the game's scripts. Witnesses are annotations, not presets.
3. Leave **Explicit supporting flags** blank to keep every other flag unchanged. If you have independently established supporting values, enter a JSON object keyed by exact developer/CT identifiers. Unknown names and out-of-range values are rejected.
4. Alternatively, **Read and apply profile** accepts an `rf4s-progress-v1` profile. If it contains `REG_MAIN_SCENARIO`, it **stages** the target and all supplied flags in the planner for review before applying them. Non-story profiles use a separate explicit confirmation.
5. Review the entire preview: named edits, event banks, candidate gates, script comparisons, warnings, omitted actions and changed-byte masks.
6. Check **I understand this does not reconstruct a playable checkpoint**. A decrease additionally requires **Allow rewind**. These acknowledgements are initially off and reset after applying/clearing the form.
7. Apply, or export the acknowledged draft through the normal pending-edit batch. Invalid JSON, invalid flags or an invalid other pending edit leave all working bytes/history unchanged and retain the drafts. Prefer **Save as…** for a test copy rather than immediately replacing the active slot.
8. Test the exported copy in-game, including loading, relevant map transitions, sleeping/day changes, affected NPCs, event selection and saving/reloading. Keep the original backup until those checks succeed. Undo changes memory only; it does not restore an already exported disk file.

Save this example as a JSON profile for **Read and apply profile**, not for the **Explicit supporting flags** field. It demonstrates input syntax, **not a recommended gameplay preset**:

```json
{
  "format": "rf4s-progress-v1",
  "label": "Numeric threshold experiment — not a checkpoint",
  "flags": {
    "REG_MAIN_SCENARIO": 440
  }
}
```

It requests only stage 440. It does **not** clear Memories' completion bit, select the event or set its participants. If you explicitly supply the main register in supporting flags too, it must equal the chosen target; disagreement is rejected rather than silently choosing one value.

### Legacy browser

Enable flag editing and acknowledge jump dependencies. Enter a target and review **Jump effects and unresolved dependencies**. To apply a staged profile/donor snapshot together with that target, check **Include the staged named-flag profile in this jump**. The combined preview and Apply use exactly those named values; the profile's own stage must match the target. Successful combined application consumes the profile.

The standalone **Apply staged flags** button also uses the planner's guard when the profile contains a main-story value. A profile that rewinds needs the separate rewind checkbox. The profile preview shows the same dependency explanation. Flag-only profiles without a main register remain ordinary named edits.

## Preview fields and limits

| Preview item | Meaning and limits |
| --- | --- |
| Direction | `advance`, `rewind`, or `unchanged` relative to **current working bytes**, not the originally opened save. `unchanged` can still include supporting-flag edits. |
| Explicit fields | All requested values, including unchanged ones. No flag is added merely because its name sounds like a prerequisite. |
| Byte diff | Exact net changes in the flag blob, with before/after bytes and an XOR mask of changed bits. Checksums are rebuilt separately on export. |
| RSV / NOW / AFTER | Reserved, running and most recently finished **event bank IDs**. AFTER is not completion history. |
| Candidate conditions | Before/after numeric and not-completed tests for The Running Sign and Memories. A failing known test makes that candidate condition false; otherwise overall eligibility is **unknown**, because participant-enable runtime queries are unresolved. |
| Witness comparisons | A **partial** list of saved writes observed around an exact stage. Differences are warnings, not proof of corruption and not an automatic repair list. |
| Missing/mismatched symbols | Checks become unknown; the planner does not reinterpret a shifted imported symbol as the audited field. |
| Omitted actions | Runtime work and records that this offline operation will not execute/copy. |

The Running Sign requires progress ≥139, its completion bit clear and nine participant-enable queries. Memories requires progress ≥440, its completion bit clear and six queries. **Do not turn those queries into guessed friendship thresholds.** A completion bit set while NOW still names the event is disclosed as a suspected contradiction, not a universal invalid-save rule.

## Exact-stage comparisons

| Stage | Recorded script witness | What the planner does not claim |
| --- | --- | --- |
| 2 / 7 | Opening name-entry / rest-dialogue milestones | Not new-game or whole-scene initialization. |
| 430 | Ending-path marker | Does not replay the ending, set the separate system flag or award `beatRF4`. |
| 440 | Memories progress threshold | Not event selection, event start or event completion. |
| 442 | Memories closing milestone, followed by `FinishCurrentSubEvent` | The preview compares Memories completion=1, AFTER=96, NOW=0 and two finish-handler clears. Matching these does not execute participant resets, the 49 shared-field resets, goals/request/NPC cleanup or timer removal. |
| 511 | Final epilogue-path marker | The preview checks two documented Ventuswill-related clears. The third script clear and complete dependencies are not reconstructed. It does not restore her actor/schedule, skip greeting, add 250 tourists/3000 prince points or set system bit 4. |

Other numeric values are accepted as storage values but explicitly marked as lacking a curated witness. The dependency evidence comes from an audited **PC** build; Switch planning carries an additional warning rather than asserting gameplay equivalence.

## Atomicity and validation

`web/story-jump.js` owns `previewStoryJump`, `applyStoryJump` and the shared English/Chinese explanation. Preview projects the complete edit on a copy; Apply re-plans against current working bytes, checks acknowledgements, then calls `SaveDocument.setFlags` once. Duplicate main-register input is coalesced only if its value agrees with the target. Unknown symbols, bounds and overlaps fail before publication.

Native operations are `storyJumpPreview` (read-only), `setStoryJump` (editable and allowed in atomic pending batches), and guarded story-bearing `applyProfile`. The native UI uses the same compiled algorithms as the browser. A no-op adds no undo entry and does not clear redo. Individual expert flag/raw tools remain low-level assignments, not guarded gameplay operations.

Regression checks cover all **512** numeric targets, adjacent-bit preservation, exact planned/applied byte equality, PC/Switch CRC and undo/redo, combined condition evaluation, immutable previews, explicit rewind consent, profile-stage conflicts, unknown layouts and native batch rollback. Native adapter/UI tests additionally cover profile staging, bilingual draft preservation and failed pending batches. These are synthetic byte/UI tests, **not gameplay acceptance**.

## Further validation

Playable checkpoint presets need controlled before/after saves for a named checkpoint, traced scripts and in-game round trips. Memories participant-enable handlers and the full map/NPC code that uses these fields remain unresolved. Do not treat partial witness comparisons as a “safe jump” preset.
