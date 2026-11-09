# Story flags: meanings, translations and read-only edit preview

Investigated 2026-11-09. **This is an annotation/research result, not a playable checkpoint preset.** Only this document was edited. The executable and bundle were read as data; no game launch, process attachment, original-save writes, or machine-code replay was performed. Existing dirty work was left alone.

## Evidence vocabulary and inputs

- **Physical / static verified (V):** directly parsed from the supplied game data, or an instruction/data-flow observed in the supplied executable. This does **not** mean validated in gameplay.
- **Developer description (D):** the original English identifier/Japanese description in `emdeb.bin`; a name is not proof of all consumers or consequences.
- **Upstream analysis (U):** the pinned modkit author's reconstruction, distinguished from independent checks below.
- **Inferred (I):** a prediction supported by those sources, not a replayed or in-game result. **Unknown (?)** means unresolved, not a default value.

The game root is `D:/Video_Game/Stand Alone Games/Rune.Factory.4.Special`. `GameSource.read()` obtains bounded, read-only byte ranges from `Bundle/Manifest.plist` and its bundles. For script/condition inspection, the pinned parsers' definitions were loaded in memory without their UI, editing entry points or sidecar discovery; no extracted game files were written.[^reader][^script-parser][^em-parser]

| Read-only input | SHA-256 of bytes inspected |
| --- | --- |
| `RF4S.exe` | `cb64f88be1f40ac932607188de85dab98c44f43a6a023c92a85e17dd18a2b803` |
| effective `emdeb.bin` | `72e02424b06f371d7eeec29b49111073d1e1af807deae7e42f45ec650fd4d4cd` |
| effective `em.bin` | `1e814fc1d8c9e7bcbc44b2087f57475741f0e725603e3bbe6e0954c558c3703e` |
| effective `rf3.mc` | `c518ecbcadec9fdd078c7b280566edfbb270f1a8cbf0e55d2ed4fd09d33a93f5` |

These fingerprints identify this investigation's local primary sources, not universal RF4S versions. All executable addresses below are **RVAs**, not file offsets.[^exe][^symbols][^em-data][^script-data]

## 1. Physical layout is stronger evidence than a flag's label

**V:** the save serializer at `0x7E798..0x7E7C7` copies the live packed bit buffer to slot offset `0x1E8C4`; the copied byte count is `((header[0] + header[1] + 31) >> 5) * 4`. Thus the symbol's bit offset can index this copied blob in the audited PC serialization. The vendor module's old top-level warning that the save uses a different serialization is not the mapping to use for this executable.[^exe][^vendor]

**V:** `REG_MAIN_SCENARIO` is bit offset **0**, width **9**; `REG_SUBEV_RSV/NOW/AFTER/DAY_COUNT/HOUR_COUNT` are respectively **153/162/171/180/189**, each width **9**, in the actual `EMDb` records. Bits inside bytes are addressed LSB-first, but the first bit of a multibit register is its **most significant value bit**: `0x241210..0x241280` starts the value mask at `1 << (width-1)` and shifts it down while incrementing the physical bit ID.[^symbols][^exe][^vendor]

Consequently a physical bit `b` maps to `save[0x1E8C4 + (b >> 3)]`, mask `1 << (b & 7)`. A nine-bit main-story edit touches the first byte and **only bit 0 of the next byte**; it must preserve the neighboring register. `0..511` is the storage range, not a list of 512 validated checkpoints. Existing `ProgressCatalog` enforces this main-register width, but its two marker labels at 430/511 are annotations rather than gameplay validation.[^exe][^symbols][^progress]

## 2. Main story: a guarded numeric register, not a complete world state

**V:** opcode **651**, `AdvanceStoryProgress`, handler `0x21DB10..0x21DB97`, reads nine bits at offset zero. `cmp ebx,eax; jbe` at `0x21DB79..0x21DB7B` makes its comparison **unsigned and strictly greater-than**. Only an advance calls writer `0x1D6000` with encoded field `0x8000`, then updates a separate live story cache at `0xE94F70`. In states masked by `0x401000`, this handler treats current progress as zero. An offline write is neither this guarded operation nor an update of that live cache; a rewind can leave later flags/world records behind.[^exe][^opcodes]

### Concrete stage witnesses (V unless explicitly marked)

| Value | Conservative English / 中文 annotation | Primary witness and limit |
| --- | --- | --- |
| 2 | Opening name-entry milestone / 开场姓名输入节点 | Primary bank 211, PC `0x14FA`: follows `OpenMenu(4)` and `OpenMenu(90)`; upstream identifies progress 2 with opening name entry. Not a full new-game preset.[^script-data][^opcodes] |
| 7 | Opening rest-dialogue milestone / 开场休息对话节点 | Bank 211, PC `0x4744`; upstream example contains dialogue #65195–65196 about resting before the advance. Exact whole-scene prerequisite set not audited.[^opcodes][^script-data] |
| 430 | Ending-path marker / 结局流程节点 | Bank 222, PCs `0x26F6` = op 667, `0x26FA` = op 651(430), followed by fade/time/NPC-plan operations. **In this local bank the system flag is set before, not after, the progress advance**; earlier prose saying “after 430” is too literal.[^script-data][^opcodes] |
| 440 | Memories eligibility threshold / “回忆”候选条件的进度门槛 | Bank 224, PC `0x7CC`, writes 440; `em.bin` entry 214 condition requires progress ≥440, plus other conditions below. Not synonymous with “Memories already completed.”[^script-data][^em-data] |
| 442 | Memories closing milestone / “回忆”收尾节点 | Bank 96, PC `0x2144`: advance(442), then `FinishCurrentSubEvent` at `0x214A`. Several `FLG_SUB_T_*` participant flags are cleared immediately before it. An edit of 442 does not run that finish handler.[^script-data] |
| 511 | Final epilogue-path marker / 最终尾声流程节点 | Bank 224, PCs `0x6F0..0x71C`: clear three Ventuswill state flags, apply her schedule, skip greeting, add 250 tourists and 3000 prince points, set system bit 4, then advance(511). These adjacent script operations are **not automatic side effects of writing 511**.[^script-data][^opcodes] |

These are witnesses, not a complete stage-name dictionary. Values are sparse and some scripts offer alternative advances; there is no evidence here that changing the register alone reconstructs an act, boss result, reward, location or NPC schedule.[^script-data][^opcodes]

### New executable side effect: the story writer is not pure

**V:** writer `0x1D6000` compares encoded field `0x8000` and proposed value **≥430** at `0x1D6288..0x1D6296`. When system config bit `0x40` is clear, that path uses the ASCII key **`beatRF4`** at RVA `0x4E63F0` and calls the `0x247C60 → 0x3E8540 → 0x3E9180 → 0x248070` wrapper before ordinary packed storage. **I:** this is an achievement-related path; actual platform award behavior is not established by this static inspection. A file edit cannot be described as awarding that achievement.[^exe]

**V/U distinction:** op 667's executable setter writes system buffer **`0xE704B0` bit 0**, corresponding to persisted offset **`+0x10`**. Re-auditing the complete RIP-relative instruction corrects this document's earlier `0xE704A8` / `+8` claim; the upstream `+0x10` offset agrees with the executable. `+8` is a save-slot availability bitmap, not the config word. Upstream supplies the Extra Orders interpretation. System bit 4 has at least a simple script-query reader (`0x21F6A0..0x21F6B6`); its downstream gameplay meaning remains unknown.[^exe][^opcodes][^prior]

## 3. Town events: reserved → running → recently finished, plus separate history

The **D** descriptions are `候補` (candidate) for RSV, `進行中` (running) for NOW, and `最近のクリア` (most recently cleared) for AFTER. They are **bank IDs**, not a shared “quest stage” number: the ordinary town-event table maps bank `48+i` to condition entry `166+i`, for `i=0..95` (bank 48–143). Zero is treated as no active/reserved event by the handlers below.[^symbols][^subevents][^exe]

1. **Selection (V):** in `0x1EDAB0..0x1EDEB2`, the nightly picker queries condition A of entry 174; a true result bypasses the failing 80% roll and finally replaces the pick with slot 8, bank **56**. Entry **214** replaces ordinary candidates with slot 48, bank **96**; otherwise eligible marriage entries **225–236** replace ordinary candidates as a group. Entry 174 has final priority over both. Selected slot +48 is written to RSV at `0x1EDE8C..0x1EDE94`; the picker also reevaluates the chosen condition with participant-recording state and queues companion departures, then dispatches entry 51. This is not an unconditional “80% any event starts” rule.[^exe][^subevents]
2. **Start (V):** op **536**, `0x2188D0..0x218A3E`, does nothing unless NOW=0 and RSV≠0 (normal game state). It clears request-array word-0 bit `0x2`, writes NOW=RSV and RSV=0, dispatches **entry 51 (`EV_SUBEV_INIT`)**, sets request bit `0x4`, dispatches `bank+118` for IDs 25–143, clears scene-control bit `0x200000`, zeros day/hour registers, and installs a calendar callback in the first available of eight slots.[^exe][^opcodes][^em-data]
3. **While running (V):** callback `0x1FA3A0..0x1FA416` checks NOW≠0 and increments `REG_SUBEV_HOUR_COUNT` **only while below 500**. A value already ≥500 is left as-is, not clamped down. The developer names the other register an elapsed-day count; its full increment/reset timing was not traced here.[^exe][^symbols]
4. **Finish (V):** op **549**, body `0x218A40..0x218CBD`, first tests NOW≠0. At `0x218A8F..0x218ACA` it sets **absolute zone-1 bit `1224 + NOW`**—there is no zone-2 base addition here. It writes AFTER=NOW (`0x80AB`), NOW=0, clears `FLG_QUEST_GEN_STOP` (334), dispatches entry 51, clears request bit `0x4` and `FLG_BOSS_NOT_SPAWN` (1426), refreshes NPC schedules, empties the 20×24-byte goal queue, clears NPC record fields/flags and several packed NPC ranges, adds category-5 prince points unless config `0x40`, and removes the calendar callback. Its code does **not** explicitly clear RSV or the day/hour registers in that closing path.[^exe][^symbols][^opcodes]

**New data-level dependency (V):** `EV_SUBEV_INIT` is not a symbolic no-op. Its 49 actions at `em.bin` `0x4776..0x48F6` clear `FLG_SUBEV_A..Z`, `REG_SUBEV_U2/U4/U8` A–D, five `REG_SCDLSET_NPC_*` / `REG_SCDLSET_SCDLID_*` pairs, and `FLG_SUBEV_AIRSHIP_STOP`. Thus start/finish/selection include shared working-register and schedule-override resets that a direct RSV/NOW/AFTER edit omits.[^em-data]

**U:** a reserved event's map-scene entry type 39 or NPC reaction entry type 27 can run op 536; running reactions use priority 1 instead of reserved priority 0. The diary chooses its title using NOW−48. This investigation independently found the diary's title-switch PC `0x4C92` in the global bank and the English/Chinese title lines below; the complete trigger routing was not independently replayed.[^subevents][^script-data][^text]

### Two high-value events with actual conditions, not guessed dependencies

| Event | Verified bank / entry / completion bit | Condition A in the shipped `em.bin` |
| --- | --- | --- |
| **The Running Sign / 会跑的广告牌** | Bank 56 / entry 174 (`EV_SUBEV_COM_09`) / bit **1280**, `FLG_SUBEV_COM_09_CLEAR`; diary dialogue **#660** | At `0x3984..0x39CB`: completion=0 **AND** progress≥139 **AND** nine enable queries=1: Dolce, Forte, Illuminata, Amber, Vishnal, Clorica, Dylas, Doug, Xiao Pai.[^em-data][^symbols][^text] |
| **Memories / 回忆** | Bank 96 / entry 214 (`EV_SUBEV_COM_49`, developer JP `エピローグ１`) / bit **1320**, `FLG_SUBEV_COM_49_CLEAR`; diary dialogue **#705** | At `0x40E2..0x4114`: progress≥440 **AND** completion=0 **AND** six enable queries=1: Arthur, Kiel, Dolce, Dylas, Amber, Leon.[^em-data][^symbols][^text] |

All listed expressions in each single condition-A way have the OR-next bit clear, so these are conjunctions, not alternative participant lists. The exact current-state meaning of every `SUBEV_ENABLE_*` query is **?** here; do not silently convert it into a friendship threshold. Setting a completion flag to 1 makes that particular eligibility condition false, but does not execute the event, grant its rewards or clear its live state. Clearing it permits reevaluation, not a guaranteed restart. If both events are eligible, the executable's forced Running Sign slot outranks Memories.[^em-parser][^em-data][^exe]

Completion and AFTER are genuinely distinct: NOW=56 finishes to AFTER=56 plus bit1280=1; NOW=96 finishes to AFTER=96 plus bit1320=1. AFTER alone is not a history bitset, and clearing NOW alone is not FinishCurrentSubEvent. Do not generalize developer completion names over every bank 48–143: the named `FLG_SUBEV_*_CLEAR` sequence stops at bit1355; at bit1356 the symbol table changes to `FLG_RQ_VIZNAR_1_CLEAR`, even though the handler's arithmetic itself has no such semantic boundary.[^exe][^symbols]

## 4. Curated English + Chinese labels

The following are **proposed UI wording**, not claims that their Chinese labels already exist in the editor. Preserve the developer identifier and attach the evidence level to the description. Official game wording is used for event titles, `沃尔卡农` (NPC entry 3), `赛尔泽薇德` (NPC entry 21), and `符文之息` (Rune Prana map-name entries 727 onward); other wording is a conservative translation.[^text][^symbols]

| Identifier / bit(s) | English / 中文 | Safe annotation and confidence |
| --- | --- | --- |
| `REG_MAIN_SCENARIO`, 0–8 | Main story progress register / 主线剧情进度寄存器 | Numeric stage only, 0–511; bypasses the live advance guard when edited. **V/D**.[^symbols][^exe] |
| `FLG_SCENARIO_END`, 28 | Final scenario flag (developer description) / 最终剧情标志（开发者描述） | JP `最後のシナリオフラグ`. **D**, physical position **V**; do not label “all endings completed” or equate it with stage511/system bit0. Consumers not traced.[^symbols] |
| `FLG_SCENARIO_EP_START_1/2`, 77/78 | Epilogue start latch 1/2 / 尾声启动标记1/2 | **D**, with writes in bank224 at `0x748/0x77E`; not an entire third-act preset. **V**.[^symbols][^script-data] |
| `FLG_SCENARIO_EP_START_1_DAY/2_DAY`, 79/80 | One day after epilogue latch 1/2 / 尾声标记1/2设置后已过一天 | **D**; global bank PCs `0x8AD0..0x8AE0` set these when the corresponding latch is1. Full day-transition invocation not independently traced. **V/?**.[^symbols][^script-data] |
| `REG_SUBEV_RSV`, 153–161 | Reserved town-event bank / 已预约的城镇事件脚本编号 | A selection awaiting its scripted starter; not “event running.” **V/D/U**.[^symbols][^exe][^subevents] |
| `REG_SUBEV_NOW`, 162–170 | Running town-event bank / 进行中的城镇事件脚本编号 | Direct edit does not initialize participants/goals/timer. **V/D**.[^symbols][^exe] |
| `REG_SUBEV_AFTER`, 171–179 | Most recently finished town-event bank / 最近完成的城镇事件脚本编号 | Last-finished ID, not all-event completion. **V/D**.[^symbols][^exe] |
| `FLG_SUBEV_COM_09_CLEAR`, 1280 | The Running Sign completed / “会跑的广告牌”完成记录 | **V**, separate completion record; controls entry174 eligibility.[^symbols][^em-data][^text][^exe] |
| `FLG_SUBEV_COM_49_CLEAR`, 1320 | Memories completed / “回忆”完成记录 | **V**, controls entry214 eligibility; does not itself write442/finish the running event.[^symbols][^em-data][^text][^script-data] |
| `FLG_SYELZA_ERACE`, 2472 | Ventuswill absent-state flag / 赛尔泽薇德不在场状态标志 | **D** `セルザいない状態`; final bank224 explicitly clears it before511. **V**. Clearing alone is not NPC restoration.[^symbols][^script-data] |
| `FLG_SYELZA_SUBEV_STOP`, 1017 | Suppress town events involving Ventuswill / 暂停涉及赛尔泽薇德的城镇事件 | **D** explicitly says not to start events in which she participates; final bank224 clears it. Complete consumers **?**.[^symbols][^script-data] |
| `CT_BIT_4166`, zone2 relative70 | Volkanon bridge hidden-state bit (CT) / 沃尔卡农桥隐藏状态位（CT参考） | Physical **V**, label from **CT**; banks132–135 clear70 and set71 together. The coupled transition is script-verified; full collision/visibility consequences remain **I/?**.[^ct][^script-data][^opcodes] |
| `CT_BIT_4167`, zone2 relative71 | Volkanon bridge passability bit (CT) / 沃尔卡农桥通行状态位（CT参考） | Same paired witness; do not rename it generically “bridge unlocked” or edit only one as a supported checkpoint.[^ct][^script-data][^opcodes] |
| `CT_BIT_4340`, zone2 relative244 | Rune Prana locked-state bit (CT) / 符文之息封锁状态位（CT参考） | Physical **V**, meaning/polarity **CT**, not independently proven map behavior. Bank211 `0x248` sets relative244 to1. Do not promise that0 alone opens a playable dungeon.[^ct][^script-data][^opcodes][^text] |
| system config bit0, system byte16 mask1 | Ending / Extra Orders system flag / 结局记录／额外指令系统标志 | Setter **V**, Extra Orders meaning **U**; shared system state, not a slot's story register.[^exe][^opcodes][^prior] |
| system config bit4, system byte16 mask16 | Final-path system bit4 (meaning unresolved) / 最终流程系统位4（用途未明） | Setter/query **V**, associated with511 in script **V**; no invented unlock label.[^exe][^script-data][^opcodes] |

Bridge polarity caution: opcode443's first two operands are relative zone2 bit ID and set/clear value; the handler adds the zone2 base. Bank211 initially sets70/73, while banks132–135 clear70/73 and set71/74. The existing CT descriptions imply hide/passability roles, but tracing every map consumer is a separate task. Physical corroboration alone does not validate a CT label.[^exe][^opcodes][^script-data][^ct]

## 5. Safe, read-only “effect of edit” preview wording

**Proposal (I):** preview a diff on a cloned flag blob, without modifying/exporting a save or applying inferred dependencies. Show identifier, evidence level, before→after value, physical bits/masks, and explicitly separate **direct byte effect**, **condition result**, **omitted runtime actions** and **unknown gameplay effects**. Existing register helpers and `ProgressCatalog.entries()` can supply bounds/identity validation, not gameplay proof.[^vendor][^progress]

Suggested examples:

- **`REG_MAIN_SCENARIO: 442 → 430`** — “Rewinds the stored numeric register. The game's normal advance command would refuse this decrease. Later completion/NPC/reward state is not rewound.” / “仅回退存储的剧情数值；游戏正常推进指令会拒绝这种回退。后续完成记录、角色和奖励状态不会随之回退。” **V-derived preview**, not a safety approval.[^exe][^script-data]
- **`REG_MAIN_SCENARIO: 430 → 440`** — “The progress test for Memories becomes true. Its completion and six participant-enable conditions still apply. No event is started or completed.” / “满足‘回忆’的进度条件；仍需未完成标志及六个参与角色条件。不会自动开始或完成事件。” Overall eligibility remains **unknown** until the queries are resolved.[^em-data][^exe]
- **`FLG_SUBEV_COM_49_CLEAR: 0 → 1`** — “Records Memories as completed for this flag; its candidate condition becomes false. Does not run stage442's closing script, clear NOW, reset working flags, grant points or restore NPC schedules.” / “仅修改‘回忆’完成记录，并使其候选条件不成立；不会执行442节点的收尾脚本，也不会清空当前事件、重置工作标志、发放点数或恢复角色日程。”[^em-data][^script-data][^exe]
- **`REG_SUBEV_NOW: 96 → 0`** — “Clears the running-event ID only. Not normal completion: AFTER, completion bit1320, goals, request state and NPC cleanup are unchanged by this edit.” / “仅清空进行中的事件编号，不等于正常完成；最近完成编号、完成位1320、事件目标、请求状态和角色清理状态不会因此改变。”[^exe]
- **`CT_BIT_4166: 1 → 0`** — “Clears the CT-labelled bridge-hidden bit. Shipped scripts pair this with setting bit4167; this preview does not apply that companion change or claim bridge usability.” / “清除CT标注的桥隐藏位；原脚本还会同时设置4167位。本预览不会自动修改关联位，也不保证桥可通行。”[^ct][^script-data][^opcodes]
- **system bit0: 0→1** — “Changes the system ending/Extra Orders flag, not the slot's story. Does not replay the ending or award an achievement.” / “修改系统结局／额外指令标志，不修改存档栏位的剧情；不会重播结局或发放成就。”[^exe][^opcodes][^prior]

The preview should flag suspected contradictions, not “repair” them automatically: e.g. NOW=96 with completion1320=1, or a changed AFTER with unchanged completion history. Because event-specific readers can have additional purposes, even these warnings are **I**, not universal invalid-save rules.[^em-data][^exe]

## 6. Candidate machine-code regression seam (not implemented or executed)

**Proposal grounded in V:** isolate the packed-register/read/guard seam instead of replaying an ending or an entire town event. Use the exact executable fingerprint above; a different build requires re-auditing. Existing appearance/relationship replay tests demonstrate the project's allowlisted, synthetic-memory approach, but are unrelated coverage and were not rerun or edited here.[^exe][^replay]

1. Pure read oracle: `0x241210..0x241280`, supplied with a synthetic `{zone2_base=4096, zone2_size=2560, bit_buffer_pointer}` header and 832-byte cloned buffer. Exercise widths9 at offsets0/153/162/171, cross-byte cases, and preservation of adjacent fields. Expect MSB-first register values, unlike a little-endian integer extraction.[^exe][^symbols][^vendor]
2. Guard oracle: handler `0x21DB10..0x21DB97`, using a well-formed VM argument array (not its missing-argument fallback). Allow the real packed-reader chain; intercept/log the **call to `0x1D6000`** without executing platform code. Test proposed values less than/equal to/greater than current, including429/430/440/442/511; also separately test state mask `0x401000`. Assert no writer/cache change for equal/decreased values; for an advance, writer arguments `(0x8000, proposed)` and cache `0xE94F70`=proposed. This seam deliberately does not prove serialized bytes are written or a story is playable.[^exe][^opcodes]
3. Optional byte-write oracle: independently audit/use `0x1D7570..0x1D760D` and its unsigned leaf `0x241290`, rather than treating `0x1D6000` as pure. A fuller writer replay must intercept the `beatRF4` external wrapper and fail closed on all unexpected calls. An allowlist copied from only `inspect_executable.py --function` is insufficient: `.pdata` unwind ranges split some logical bodies (e.g. op549's initial range ends at `0x218A59`, despite reachable code through `0x218CBD`).[^exe][^inspector]
4. Optional lifecycle trace: audit/log op536/549 calls to the packed writer, entry51 and schedule/points APIs, using synthetic request/NPC/calendar records. Include entry51's 49 actual resets and completion-bit arithmetic in the expected trace. A stubbed trace is **not** a test of real participants, event goals, calendar behavior or map playback.[^exe][^em-data]

No whole playable checkpoint presets are justified here. The concrete next research targets are the six Memories enable-query handlers, the map consumers of zone2 bits70/71/244, and controlled before/after event saves supplied by the user—not automatic dependency writes based on translated labels.[^em-data][^ct][^script-data]

## Primary-source references

[^exe]: Local primary executable: `D:/Video_Game/Stand Alone Games/Rune.Factory.4.Special/RF4S.exe`, SHA-256 above; static PE reads and Capstone instruction inspection with [`scripts/inspect_executable.py`](../scripts/inspect_executable.py). Exact audited RVAs are given beside each claim; no executable launch or emulation occurred in this investigation.
[^symbols]: Local effective `Bundle` member `emdeb.bin` (hash above), parsed with [`vendor/rf4-modkit/emflags.py`](../vendor/rf4-modkit/emflags.py) `EmFlagTable.parse(..., extra=False)`. Variable records start at header word7+4, stride24; fields are name pointers, bit offset, and width in metadata byte1. Cross-check: [`web/save-metadata.js`](../web/save-metadata.js), `symbols`. Developer Japanese strings quoted in this document were reread from the actual bundle.
[^em-data]: Local effective `Bundle` member `em.bin` (hash above), decoded with pinned [`rf4s_modkit/emscript.py`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/emscript.py), `EmScript.parse()` and `EmNames.parse()` using actual `emdeb.bin`. Entry174 condition PCs `0x3984..0x39CB`, entry214 `0x40E2..0x4114`, entry51 action PCs `0x4776..0x48F6`; these are **em.bin byte offsets**, not exe RVAs.
[^script-data]: Local effective `Bundle` member `rf3.mc` (hash above), statically decoded by the pinned parser's `Container`, `disassemble_bank`, `decode_statement`, `disasm_expr` and symbol resolver. References in this document use **bank-local bytecode PCs**. Useful primary-bank file bases: 96=`0x166165`, 211=`0x263E49`, 222=`0x2A3D32`, 224=`0x2B0668`. No scripts were run.
[^text]: Local effective `Bundle` language members `rf3mc.eng`, `rf3mc.chn`, `rf3TxtNpc_split2_1.chn`, and `rf3TxtMapName.chn`: TEXT record index gives `(size, offset)` at `8+8*index`, UTF-8 payload. Global diary switch PC `0x4C92`: title rows #660 and #705; the respective exact English/Chinese texts are `[Current Event]\nThe Running Sign` / `【进行中的事件】\n会跑的广告牌` and `[Current Event]\nMemories` / `【进行中的事件】\n回忆`. NPC/map indices are stated above. These are official local-game strings, not fan translations.
[^reader]: [`scripts/game_sources.py`](../scripts/game_sources.py), `GameSource.__init__`, `read`, `parse_text`; effective bundle ordering and file bounds are implemented here. Large dialogue TEXT tables were read using their indexed records, not the small-reference-table count cap.
[^vendor]: [`vendor/rf4-modkit/emflags.py`](../vendor/rf4-modkit/emflags.py), old save caveat lines22–26, two-zone store description, `read_value`/`write_value`; pinned original [`rf4s_modkit/emflags.py`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/emflags.py). Treat the save caveat as superseded only for the locally audited serializer, not every platform/version.
[^script-parser]: Pinned [`rf4s_modkit/script.py`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/script.py), `Container`, `Bank`, expression/statement decoders, flow-following disassembler; this owns the parsing rules used for bytecode witnesses.
[^em-parser]: Pinned [`rf4s_modkit/emscript.py`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/emscript.py), operand/expression model, `Expr.or_next`, condition semantics and `EmScript.parse`.
[^opcodes]: Pinned [`refdata/opcode_table.json`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/refdata/opcode_table.json), action rows443–445, 536, 549, 651, 666–671 and row16's opening-name evidence. Source descriptions are reverse-engineering analysis, not developer documentation; offsets and ordering were independently checked where marked V.
[^subevents]: Pinned [`rf4s_modkit/subevents.py`](https://github.com/arryndoestech/rf4-modkit/blob/799828a433d0e5be537b977918d5a7c773ad1200/rf4s_modkit/subevents.py), module lifecycle notes, FIRST_BANK/FIRST_ENTRY/COUNT, `special_rule`, `participants`, `starters`, `diary_titles`.
[^ct]: Supplied `Rune Factory 4 Special Steam v13_happy.CT`, inert single-bit descriptions retained in [`web/save-metadata.js`](../web/save-metadata.js), `ctFlags`: bits4166/4167/4340. Existing [physical CT/save mapping evidence](cheat-table-and-platforms.md#useful-ct-findings) corroborates location, not every semantic label. The original CT was not executed or modified.
[^progress]: [`web/progress-core.js`](../web/progress-core.js), `STORY_MARKERS`, `ProgressCatalog` constructor/entries/snapshot; existing implementation describes supported numeric editing and scopes, not dependency reconstruction.
[^prior]: Existing [`docs/cheat-table-and-platforms.md`](cheat-table-and-platforms.md#system-flags), system base/CRC/flag audit and story/subquest limits. Refer to the primary executable and pinned opcode rows above for new corrections rather than treating this prior note as sole semantic evidence.
[^replay]: Existing [`tests/replay_appearance.py`](../tests/replay_appearance.py), `AUDITED_EXE_SHA256` and instruction allowlist; [`tests/replay_relationships.py`](../tests/replay_relationships.py), synthetic NPC records and escaped-path rejection. These files were read only, may be ongoing user work, and were not modified.
[^inspector]: [`scripts/inspect_executable.py`](../scripts/inspect_executable.py), `.pdata` range selection in `function_at()`. Static inspection of the local body identifies the longer reachable op549 range; do not confuse an unwind segment with the complete logical function.
