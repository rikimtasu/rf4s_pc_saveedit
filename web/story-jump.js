// Dependency-aware offline flag assignment, not a script runner or checkpoint generator.
import { FLAGS_OFFSET, FLAGS_BITS, STORY_REGISTER, integer, readFlag, writeFlag } from './save-core.js';
import { SAVE_METADATA } from './save-metadata.js';
import { flagHelp, storyConditions, STORY_WITNESSES } from './flag-help.js';

const audited = new Map([...SAVE_METADATA.symbols, ...SAVE_METADATA.ctFlags].map(field => [field.name, field]));
const note = (code, en, zh) => ({ code, en, zh });
// Only the two documented adjacent flag clears. Not an all-unlocks preset.
export const ENDGAME_SHORTCUT = { target: 511, flags: { FLG_SYELZA_ERACE: 0, FLG_SYELZA_SUBEV_STOP: 0 }, label: 'Experimental end-game flags · not world initialization' };

export function previewStoryJump(save, catalog, options = {}) {
  save.requireSlot();
  const target = integer(options.target, 0, 511, 'Main story stage');
  const entries = catalog.entries(options.flags === undefined ? {} : options.flags);
  const main = catalog.byName.get(STORY_REGISTER.name);
  if (!main || main.bitOffset !== 0 || main.width !== 9) throw new Error('Unexpected main-story register.');
  const suppliedMain = entries.find(entry => entry.variable.name === main.name);
  if (suppliedMain && suppliedMain.value !== target) throw new Error('Profile story stage conflicts with the jump target.');
  if (!suppliedMain) entries.unshift({ variable: main, value: target });

  const before = save.data, after = before.slice(), used = new Set();
  const fields = entries.map(({ variable, value }) => {
    // Validate the complete edit list before publishing anything, even for custom catalogs.
    for (let bit = variable.bitOffset; bit < variable.bitOffset + variable.width; bit++) {
      if (used.has(bit)) throw new Error('Progress edits overlap.');
      used.add(bit);
    }
    const from = save.flag(variable);
    writeFlag(after, variable, value);
    return { name: variable.name, bitOffset: variable.bitOffset, width: variable.width, from, to: value, changed: from !== value, help: flagHelp(variable) };
  });
  const changes = [];
  for (let offset = FLAGS_OFFSET; offset < FLAGS_OFFSET + FLAGS_BITS / 8; offset++) {
    if (before[offset] !== after[offset]) changes.push({ offset, before: before[offset], after: after[offset], mask: before[offset] ^ after[offset] });
  }
  const from = readFlag(before, main), direction = target < from ? 'rewind' : target > from ? 'advance' : 'unchanged';
  const warnings = [];
  const read = (bytes, name) => {
    const field = catalog.byName.get(name), expected = audited.get(name);
    return field && expected && field.bitOffset === expected.bitOffset && field.width === expected.width ? readFlag(bytes, field) : null;
  };
  const beforeEvents = Object.fromEntries(['REG_SUBEV_RSV', 'REG_SUBEV_NOW', 'REG_SUBEV_AFTER'].map(name => [name, read(before, name)]));
  const afterEvents = Object.fromEntries(Object.keys(beforeEvents).map(name => [name, read(after, name)]));
  if (direction === 'rewind') warnings.push(note('rewind', 'The normal game command refuses a decrease. Later world, reward and completion records are not rewound.', '游戏正常推进指令会拒绝降低进度。后续世界、奖励及完成记录不会随之回退。'));
  if (direction !== 'unchanged' && (beforeEvents.REG_SUBEV_NOW > 0 || beforeEvents.REG_SUBEV_RSV > 0 || afterEvents.REG_SUBEV_NOW > 0 || afterEvents.REG_SUBEV_RSV > 0)) warnings.push(note('event-in-flight', 'A running or reserved town event exists before or after this jump. Its participants, goals and timer may belong to another stage.', '跳转前或跳转后有进行中／已预约的城镇事件，其参与者、目标和计时器可能属于另一剧情阶段。'));
  if (Object.values(beforeEvents).some(value => value === null)) warnings.push(note('unknown-event-layout', 'Town-event register layout is missing or differs from the audited symbols; event-state checks are unknown.', '城镇事件寄存器缺失或与已审计布局不符，事件状态检查结果未知。'));
  if (beforeEvents.REG_SUBEV_NOW !== afterEvents.REG_SUBEV_NOW) warnings.push(note('event-id-edit', 'Changing NOW does not run Start/FinishCurrentSubEvent: shared registers, NPC schedules, goals, requests and calendar callbacks are not initialized or cleaned.', '修改 NOW 不会执行事件开始／结束处理：共享寄存器、NPC 日程、目标、委托及日历回调不会初始化或清理。'));
  if (beforeEvents.REG_SUBEV_RSV !== afterEvents.REG_SUBEV_RSV) warnings.push(note('reserved-id-edit', 'Changing RSV bypasses the nightly picker, participant recording and companion departure setup; reservation is not an event start.', '修改 RSV 绕过夜间选择、参与者记录及队友离队安排；预约不等于开始事件。'));
  if (beforeEvents.REG_SUBEV_AFTER !== afterEvents.REG_SUBEV_AFTER) warnings.push(note('after-id-edit', 'AFTER is only the most recently finished bank ID, not completion history or proof that cleanup ran.', 'AFTER 只是最近完成的脚本编号，不是完成历史，也不证明已执行收尾。'));
  for (const gate of storyConditions(after, catalog.byName)) {
    if (afterEvents.REG_SUBEV_NOW === gate.event && read(after, gate.completed) === 1) warnings.push(note(`active-completed-${gate.event}`, `${gate.name}: NOW still names this event while its completion bit is set. This is a suspected contradiction, not a universal invalid-save rule.`, `${gate.zh}：NOW 仍指向该事件，但完成位已设置。这是疑似矛盾，不是通用的存档无效规则。`));
  }
  const observedWrites = target === 442 ? { FLG_SUBEV_COM_49_CLEAR: 1, REG_SUBEV_AFTER: 96, REG_SUBEV_NOW: 0, FLG_QUEST_GEN_STOP: 0, FLG_BOSS_NOT_SPAWN: 0 }
    : target === 511 ? { FLG_SYELZA_ERACE: 0, FLG_SYELZA_SUBEV_STOP: 0 } : {};
  const witnessChecks = Object.entries(observedWrites).map(([name, expected]) => {
    const value = read(after, name);
    return { name, expected, value, matches: value === null ? null : value === expected };
  });
  if (witnessChecks.some(check => check.matches !== true)) warnings.push(note('witness-mismatch', 'Some saved fields differ from operations observed beside this exact stage in the audited script. The list is partial and is not an automatic repair preset.', '某些存储字段与已审计脚本中此节点附近的操作不一致。此列表不完整，不是自动修复预设。'));
  const witness = STORY_WITNESSES.find(item => item.value === target) || null;
  if (!witness) warnings.push(note('unannotated-stage', 'No curated script witness exists for this value. Storage range is not checkpoint validation.', '此数值没有人工整理的脚本节点证据。可存储范围不代表检查点已验证。'));
  const omitted = [note('runtime', 'No cutscenes, map/party initialization, NPC records/schedules, request payloads, event cleanup or rewards are replayed or copied.', '不会重播／复制过场、地图／队伍初始化、NPC 记录／日程、委托数据、事件收尾或奖励。')];
  if (fields.length > 1) warnings.push(note('explicit-profile-scope', 'Only explicit profile flags are copied. Broad/all-flags profiles may also change relationships, discovery, chests and unlocks without their corresponding records. No omitted prerequisite is inferred.', '只复制档案中明确指定的标志。宽范围／全标志档案还可能改变关系、发现、宝箱及解锁标志，却不复制对应记录。不会推断遗漏的前置条件。'));
  if (target >= 430) omitted.push(note('system', 'The separate system save is untouched. Ending/system bits and the beatRF4 achievement-related runtime path are not executed.', '独立的系统存档保持不变。不会执行结局／系统标志及 beatRF4 成就相关运行流程。'));
  if (target === 440) omitted.push(note('memories', '440 satisfies only the Memories progress threshold. Six participant-enable runtime queries remain unresolved; no event is selected or started.', '440 仅满足“回忆”的剧情门槛。六个参与者启用运行时查询仍未解析；不会选择或开始事件。'));
  if (target === 442) omitted.push(note('memories-finish', '442 does not execute the preceding participant resets or FinishCurrentSubEvent, even if the explicit profile matches the visible completion records.', '442 不会执行前面的参与者重置及 FinishCurrentSubEvent，即使手动指定的档案匹配可见完成记录。'));
  if (target === 511) omitted.push(note('epilogue', '511 does not restore Ventuswill, apply her schedule, skip greeting, add 250 tourists/3000 prince points or set system bit 4. Only two adjacent flag clears are checked here.', '511 不会恢复赛尔泽薇德、应用日程、跳过问候、增加 250 游客／3000 王子点数或设置系统位 4。这里只检查两个相邻的标志清除操作。'));
  if (save.platform !== 'pc') warnings.push(note('platform', 'Script dependency evidence comes from the audited PC build; Switch gameplay equivalence is unverified.', '脚本依赖证据来自已审计的 PC 版本；与 Switch 游戏行为是否等价尚未验证。'));
  return { from, target, direction, fields, changes, beforeEvents, afterEvents, beforeConditions: storyConditions(before, catalog.byName), afterConditions: storyConditions(after, catalog.byName), witness, witnessChecks, warnings, omitted, simulatedEvents: false, playableCheckpoint: 'unverified', label: String(options.label || `Story jump ${from} → ${target}`).slice(0, 120) };
}

export function applyStoryJump(save, catalog, options = {}) {
  // Always re-plan against current working bytes. Never trust an old preview's offsets/values.
  const plan = previewStoryJump(save, catalog, options);
  if (!plan.changes.length) return false;
  if (options.acknowledgeRisk !== true) throw new Error('Acknowledge incomplete story dependencies before applying a jump.');
  if (plan.direction === 'rewind' && options.allowRewind !== true) throw new Error('Explicitly allow story rewind before decreasing the stage.');
  return save.setFlags(catalog.entries(Object.fromEntries(plan.fields.map(field => [field.name, field.to]))), plan.label);
}

export function explainStoryJump(plan, language = 'en') {
  const zh = language === 'zh', text = (en, cn) => zh ? cn : en;
  const state = value => value === null ? text('unknown', '未知') : value ? text('pass', '满足') : text('fail', '不满足');
  const lines = [text('Offline story-jump preview — not a validated playable checkpoint', '离线剧情跳转预览 — 不是已验证的可玩检查点'), `${plan.from} → ${plan.target} · ${plan.direction}`, text('Only the explicit named fields below will be written:', '只会写入下列明确指定的字段：')];
  for (const field of plan.fields) {
    lines.push(`${field.name}: ${field.from} → ${field.to}${field.changed ? '' : text(' (unchanged)', '（不变）')}`);
    if (field.changed && field.name !== STORY_REGISTER.name) lines.push(`  ${field.help.title[zh ? 'zh' : 'en']} · ${field.help.evidence}\n  ${field.help.impact[zh ? 'zh' : 'en']}`);
  }
  if (plan.witness) lines.push(text('Script witness: ', '脚本节点证据：') + plan.witness[zh ? 'zh' : 'en']);
  for (const check of plan.witnessChecks) lines.push(`${check.name}: ${check.value === null ? text('unknown', '未知') : check.value} / ${text('observed', '脚本观察值')} ${check.expected} · ${state(check.matches)}`);
  lines.push(text('Town-event banks before → after:', '城镇事件脚本编号，修改前 → 修改后：'));
  for (const name of Object.keys(plan.beforeEvents)) lines.push(`${name}: ${plan.beforeEvents[name] === null ? '?' : plan.beforeEvents[name]} → ${plan.afterEvents[name] === null ? '?' : plan.afterEvents[name]}`);
  lines.push(text('Candidate conditions (not event execution):', '候选条件（不等于执行事件）：'));
  for (let i = 0; i < plan.afterConditions.length; i++) {
    const before = plan.beforeConditions[i], after = plan.afterConditions[i];
    lines.push(`${zh ? after.zh : after.name}: ≥${after.minimum} ${state(before.progressPass)} → ${state(after.progressPass)}; ${text('not completed', '未完成')} ${state(before.completionPass)} → ${state(after.completionPass)}; ${text('eligibility', '总体资格')} ${after.eligibility === 'false' ? text('false', '不满足') : text('unknown', '未知')}`);
    lines.push(text('Participant-enable runtime queries are unknown, not assumed to be friendship checks. NPC IDs: ', '参与者启用运行时查询未知，不假定为好感度检查。NPC ID：') + after.participants.join(', '));
  }
  lines.push(text('Warnings / suspected inconsistencies:', '警告／疑似不一致：'));
  for (const warning of plan.warnings) lines.push(`[${warning.code}] ${warning[zh ? 'zh' : 'en']}`);
  lines.push(text('Actions NOT performed:', '不会执行的操作：'));
  for (const item of plan.omitted) lines.push(item[zh ? 'zh' : 'en']);
  lines.push(text('Changed bytes (offset: before → after; XOR mask):', '修改字节（偏移：修改前 → 修改后；异或掩码）：'));
  for (const change of plan.changes) lines.push(`0x${change.offset.toString(16).toUpperCase().padStart(5, '0')}: ${change.before.toString(16).padStart(2, '0')} → ${change.after.toString(16).padStart(2, '0')}; 0x${change.mask.toString(16).padStart(2, '0')}`);
  lines.push(text('Preview changes no bytes or history. Apply is one undoable edit; export rebuilds the checksum, not world state.', '预览不修改字节及历史。应用是一次可撤销编辑；导出重建校验和，不重建世界状态。'));
  return lines.join('\n');
}
