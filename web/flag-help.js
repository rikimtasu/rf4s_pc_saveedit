// Offline translations / edit-impact help. Symbol interpretations are not gameplay proof.
import { SAVE_METADATA } from './save-metadata.js';
import { FLAGS_OFFSET, integer, readFlag, writeFlag } from './save-core.js';

const known = new Map([...SAVE_METADATA.symbols, ...SAVE_METADATA.ctFlags].map(field => [field.name, field]));
const DESCRIPTIONS = new Map([
  ['メインシナリオ進行レジスタ', ['Main story progress register', '主线剧情进度寄存器']],
  ['最後のシナリオフラグ', ['Final scenario flag', '最终剧情标志']],
  ['EP会話プレゼント', ['Episode conversation gift', '章节对话赠礼']],
  ['EP会話プレゼント 未使用', ['Episode conversation gift (unused)', '章节对话赠礼（未使用）']],
  ['Ｑ汎用', ['Generic request field (purpose unknown)', '委托通用字段（用途未确认）']],
  ['汎用', ['Generic field (purpose unknown)', '通用字段（用途未确认）']],
  ['双子岩８の字フラグ', ['Twin rocks figure-eight flag', '双子岩“8”字标志']],
  ['サブイベントの雑談TOGGLE用フラグ', ['Town-event conversation toggle', '城镇事件闲聊切换标志']],
  ['お年玉をあげた', ['New Year gift given', '已赠送压岁钱']],
  ['サブイベント関係者', ['Town-event participant', '城镇事件参与者']],
  ['デート回数', ['Date count', '约会次数']],
  ['デート雑貨屋で買った', ['Purchased at general store on date', '约会时已在杂货店购买']],
  ['デート鍛冶屋で買った', ['Purchased at smithy on date', '约会时已在锻冶店购买']],
  ['デート花屋で買った', ['Purchased at flower shop on date', '约会时已在花店购买']],
  ['お店技', ['Shop-related field (purpose incomplete)', '商店相关字段（用途未完全确认）']],
  ['ラブ度節目会話', ['Affection milestone conversation', '好感度阶段对话']],
  ['告白可能フラグ', ['Confession availability flag', '可告白标志']],
  ['収穫したことがある', ['Has harvested this crop', '曾收获此作物']],
  ['依頼をクリア', ['Request cleared', '委托已完成']],
  ['嫁ID', ['Spouse ID', '配偶 ID']],
]);
const TITLES = {
  REG_MAIN_SCENARIO: ['Main story progress', '主线剧情进度'],
  FLG_SCENARIO_END: ['Final scenario flag', '最终剧情标志'],
  REG_SUBEV_RSV: ['Reserved town-event ID', '预留城镇事件 ID'],
  REG_SUBEV_NOW: ['Active town-event ID', '当前城镇事件 ID'],
  REG_SUBEV_AFTER: ['Most recently completed town-event ID', '最近完成的城镇事件 ID'],
  REG_QUEST_AFTER: ['Previous request ID', '此前委托 ID'],
  REG_WIFE_ID: ['Spouse ID', '配偶 ID'],
  FLG_PROPOSE: ['Engagement-ring acceptance flag', '订婚戒指接收标志'],
  FLG_SUBEV_COM_09_CLEAR: ['The Running Sign completed', '“会跑的广告牌”完成记录'],
  FLG_SUBEV_COM_49_CLEAR: ['Memories completed', '“回忆”完成记录'],
  FLG_SCENARIO_EP_START_1: ['Epilogue start latch 1', '尾声启动标记 1'],
  FLG_SCENARIO_EP_START_2: ['Epilogue start latch 2', '尾声启动标记 2'],
  FLG_SCENARIO_EP_START_1_DAY: ['One day after epilogue latch 1', '尾声标记 1 设置后已过一天'],
  FLG_SCENARIO_EP_START_2_DAY: ['One day after epilogue latch 2', '尾声标记 2 设置后已过一天'],
  FLG_SYELZA_ERACE: ['Ventuswill absent-state flag', '赛尔泽薇德不在场状态标志'],
  FLG_SYELZA_SUBEV_STOP: ['Suppress Ventuswill town events', '暂停涉及赛尔泽薇德的城镇事件'],
  CT_BIT_4166: ['Volkanon bridge hidden-state bit (CT)', '沃尔卡农桥隐藏状态位（CT 参考）'],
  CT_BIT_4167: ['Volkanon bridge passability bit (CT)', '沃尔卡农桥通行状态位（CT 参考）'],
  CT_BIT_4340: ['Rune Prana locked-state bit (CT)', '符文之息封锁状态位（CT 参考）'],
};
const TOKENS = { FLG: '标志', REG: '寄存器', MAIN: '主线', SCENARIO: '剧情', SUBEV: '城镇事件', QUEST: '委托', RQ: '委托', REQUEST: '委托', CLEAR: '完成', CHECK: '检查', END: '结束', NOW: '当前', RSV: '预留', AFTER: '此前', COUNT: '计数', CNT: '计数', DAY: '日期', HOUR: '小时', MINUTE: '分钟', TALK: '对话', PLAYER: '玩家', BIRTH: '生日', KNOW: '知晓', MARRIAGE: '结婚', MARRIGE: '结婚', JUST: '刚', MARRIED: '新婚', DATE: '约会', LOVE: '好感', WIFE: '配偶', ID: 'ID', FES: '节日', RESULT: '结果', PRESENT: '赠礼', FREE: '闲聊', KOKUHAKU: '告白', CROP: '作物' };
const PEOPLE = { ビシュナル: ['Vishnal', '比修纳尔'], クローリカ: ['Clorica', '克罗丽卡'], ヴォルカノン: ['Volkanon', '沃尔卡农'], フォルテ: ['Forte', '芙缇'], キール: ['Kiel', '基尔'], バド: ['Bado', '巴朵'], マーガレット: ['Margaret', '玛格丽特'], ディラス: ['Dylas', '迪拉斯'], アーサー: ['Arthur', '亚瑟'], ポコリーヌ: ['Porcoline', '波克利'], シャオパイ: ['Xiao Pai', '小白'], リンファ: ['Lin Fa', '玲花'], コハク: ['Amber', '琥珀'], エルミナータ: ['Illuminata', '艾尔米娜塔'], ダグ: ['Doug', '达格'], ブロッサム: ['Blossom', '布洛瑟姆'], ドルチェ: ['Dolce', '朵露切'], ジョーンズ: ['Jones', '琼斯'], ナンシー: ['Nancy', '南希'], レオン: ['Leon', '雷昂'], セルザウィード: ['Ventuswill', '瑟尔泽薇德'], 息子: ['Son', '儿子'], 娘: ['Daughter', '女儿'] };
const ALIASES = { 'Rune Prana Locked': '符文之息封锁（CT 标签，未验证完整依赖）', 'Story Event Flags': '剧情事件标志', 'Story Barrier Flags': '剧情屏障标志', 'Dungeon Barrier Flags': '迷宫屏障标志', 'Chest Flags': '宝箱标志', 'Reference flags': '参考标志' };
const STATIC_IMPACTS = {
  FLG_SUBEV_COM_09_CLEAR: { en: 'This completion bit gates The Running Sign (event 56), which also requires story ≥139 and nine participant-enable queries. Setting it does not finish a running event; clearing it does not guarantee a restart.', zh: '此完成位控制“会跑的广告牌”（事件 56）的候选条件；还需剧情 ≥139 及九个参与者启用查询。设置它不会完成进行中的事件，清除它也不保证重启事件。' },
  FLG_SUBEV_COM_49_CLEAR: { en: 'This completion bit gates Memories (event 96), which also requires story ≥440 and six participant-enable queries. It does not execute stage 442 cleanup, update AFTER/NOW, reset shared flags or grant rewards.', zh: '此完成位控制“回忆”（事件 96）的候选条件；还需剧情 ≥440 及六个参与者启用查询。不会执行 442 节点收尾、更新最近／当前事件、重置共享标志或发放奖励。' },
  REG_SUBEV_NOW: { en: 'Changing/clearing NOW only changes the running bank ID. Normal completion also sets bit 1224 + NOW, updates AFTER, resets 49 shared fields and cleans goals, request state, NPCs and the timer.', zh: '更改／清除 NOW 仅改变进行中的脚本编号。正常完成还会设置 1224 + NOW 完成位、更新 AFTER、重置 49 个共享字段，并清理目标、委托、NPC 和计时器。' },
  REG_SUBEV_AFTER: { en: 'This is the last completed event bank, not a completion-history bitset. Changing it does not set the separate completion bit or perform cleanup.', zh: '这是最近完成的事件脚本编号，不是完整的完成历史位集。修改它不会设置独立完成位或执行收尾清理。' },
  CT_BIT_4166: { en: 'Shipped scripts pair clearing bridge bit 4166 with setting bit 4167. No companion change is applied here; CT polarity and full map behavior remain unverified.', zh: '原脚本会同时清除桥状态位 4166 并设置 4167。本编辑不会自动改关联位；CT 标注的正反含义及完整地图行为仍未验证。' },
  CT_BIT_4167: { en: 'Shipped scripts pair this bridge bit with bit 4166. Changing one flag is not a verified bridge-unlock preset.', zh: '原脚本将此桥状态位与 4166 成对修改。单独修改一位不是已验证的桥解锁方案。' },
  CT_BIT_4340: { en: 'Physical position and script write verified; locked-state meaning/polarity comes from CT. Clearing it alone is not a verified playable Rune Prana unlock.', zh: '已验证物理位置及脚本写入；封锁含义／正反关系来自 CT。单独清除它不等于已验证的“符文之息”可玩解锁。' },
  FLG_SYELZA_ERACE: { en: 'The final script clears this before stage 511 along with schedules and other flags. Clearing it alone does not restore Ventuswill.', zh: '最终脚本会在 511 节点前连同日程及其他标志清除此位。单独清除不会完整恢复赛尔泽薇德。' },
};
export const STORY_WITNESSES = [
  { value: 2, en: 'Opening name-entry milestone', zh: '开场姓名输入节点' },
  { value: 7, en: 'Opening rest-dialogue milestone', zh: '开场休息对话节点' },
  { value: 430, en: 'Ending-path marker', zh: '结局流程节点' },
  { value: 440, en: 'Memories eligibility threshold (other conditions apply)', zh: '“回忆”进度门槛（仍需其他条件）' },
  { value: 442, en: 'Memories closing milestone', zh: '“回忆”收尾节点' },
  { value: 511, en: 'Final epilogue-path marker', zh: '最终尾声流程节点' },
];
export const STORY_GATES = [
  { name: 'The Running Sign', zh: '会跑的广告牌', event: 56, minimum: 139, completed: 'FLG_SUBEV_COM_09_CLEAR', participants: [17, 4, 14, 13, 1, 2, 8, 15, 11] },
  { name: 'Memories', zh: '回忆', event: 96, minimum: 440, completed: 'FLG_SUBEV_COM_49_CLEAR', participants: [9, 5, 17, 8, 13, 20] },
];

export function flagHelp(variable) {
  const expected = known.get(variable.name);
  const layoutMatches = Boolean(expected && expected.bitOffset === variable.bitOffset && expected.width === variable.width);
  const original = variable.description || variable.label || '';
  let pair = layoutMatches ? TITLES[variable.name] || DESCRIPTIONS.get(original) : null;
  if (!pair && layoutMatches && original.endsWith('汎用')) {
    const person = PEOPLE[original.slice(0, -2)];
    if (person) pair = [`${person[0]} generic field (purpose unknown)`, `${person[1]}通用字段（用途未确认）`];
  }
  if (!pair && layoutMatches && ALIASES[variable.label]) pair = [variable.label, ALIASES[variable.label]];
  const parts = variable.name.split('_');
  const symbolic = parts.some(part => TOKENS[part]);
  const en = pair?.[0] || parts.join(' / ');
  const zh = pair?.[1] || parts.map(part => TOKENS[part] || part).join(' / ');
  const special = layoutMatches && variable.name === 'REG_MAIN_SCENARIO' ? {
    en: 'Offline assignment bypasses the unsigned advance-only guard, runtime cache and achievement-related writer path (≥430). Rewinding leaves later flags/world state behind. Numeric stages are not playable checkpoint presets.',
    zh: '离线赋值绕过无符号“只向前推进”保护、运行时缓存及 ≥430 的成就相关写入流程。回退可能残留后续标志和世界状态。数值阶段不等于可玩的剧情检查点。',
  } : layoutMatches && /^REG_SUBEV_(RSV|NOW|AFTER)$/.test(variable.name) ? {
    en: 'Town-event IDs alone do not initialize event scripts, participants, request state or calendar callbacks.',
    zh: '仅改城镇事件 ID 不会初始化事件脚本、参与者、委托状态或日历回调。',
  } : null;
  const audited = layoutMatches && (special || STATIC_IMPACTS[variable.name]);
  return { title: { en, zh }, original, translation: pair ? 'curated' : symbolic ? 'symbol interpretation' : 'unknown', evidence: layoutMatches ? variable.source ? 'CT label; semantics not independently verified' : audited ? 'Static game/script evidence; not in-game validation' : 'Developer description / symbol; not gameplay validation' : 'Unknown or mismatched layout', impact: layoutMatches && STATIC_IMPACTS[variable.name] || special || { en: 'No automatic event replay, rewards, world initialization or dependency repair.', zh: '不会自动重播事件、发放奖励、初始化世界或修复依赖。' }, sources: layoutMatches ? ['docs/story-flag-investigation.md', 'docs/cheat-table-and-platforms.md', 'vendor/rf4-modkit/emflags.py'] : [] };
}

export function storyConditions(bytes, variables = known) {
  const value = name => {
    const field = variables.get(name), expected = known.get(name);
    return field && expected && field.bitOffset === expected.bitOffset && field.width === expected.width ? readFlag(bytes, field) : null;
  };
  const stage = value('REG_MAIN_SCENARIO');
  return STORY_GATES.map(gate => {
    const completed = value(gate.completed);
    const progressPass = stage === null ? null : stage >= gate.minimum;
    const completionPass = completed === null ? null : completed === 0;
    return { ...gate, stage, progressPass, completionPass, participantState: 'unknown runtime queries', eligibility: progressPass === false || completionPass === false ? 'false' : 'unknown' };
  });
}

export function previewFlagEdit(save, variable, input) {
  save.requireSlot();
  if (!variable) throw new Error('Choose a known flag.');
  const to = integer(input, 0, 2 ** variable.width - 1, variable.name);
  const from = save.flag(variable), bytes = save.data.slice();
  writeFlag(bytes, variable, to);
  const start = FLAGS_OFFSET + Math.floor(variable.bitOffset / 8);
  const end = FLAGS_OFFSET + Math.ceil((variable.bitOffset + variable.width) / 8);
  const changes = [];
  for (let offset = start; offset < end; offset++) if (bytes[offset] !== save.data[offset]) changes.push({ offset, before: save.data[offset], after: bytes[offset] });
  return { name: variable.name, from, to, changes, rewind: variable.name === 'REG_MAIN_SCENARIO' && to < from, help: flagHelp(variable), simulatedEvents: false, beforeConditions: storyConditions(save.data), afterConditions: storyConditions(bytes), stageWitness: variable.name === 'REG_MAIN_SCENARIO' ? STORY_WITNESSES.find(witness => witness.value === to) || null : null };
}
