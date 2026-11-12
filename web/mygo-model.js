// Presentation data for the native Go widgets. All binary writes stay in native-core.
import { nativeInvoke as call } from './native-core.js';
import { GAME_LANGUAGES, languageTable, parseGameText } from './language-core.js';

let languages = {};
let icons = {};
const constants = call('constants');
const field = (key, label, kind = 'number', rest = {}) => ({ key, label, kind, ...rest });
const choice = (label, value) => ({ label: String(label), value });
const choices = entries => entries.map(([label, value]) => choice(label, value));
const bool = (key, label) => field(key, label, 'bool');
const objectFields = obj => Object.entries(obj).map(([key, spec]) => field(key, spec.label || key, 'number', spec));
const pages = [
  ['overview', 'Save overview', 'Save'], ['calendar', 'Calendar', 'Player'], ['player', 'Player values', 'Player'],
  ['inventory', 'Bag & storage', 'Player'], ['gear', 'Equipment shortcuts', 'Player'],
  ['skills', 'Skills', 'Player'], ['recipes', 'Learned recipes', 'Player'],
  ['friendship', 'Friendship', 'People'], ['relationships', 'Dating & nicknames', 'People'],
  ['people', 'People stats', 'People'], ['monsters', 'Tamed monsters', 'People'], ['marriage', 'Marriage flags', 'People'],
  ['roster', 'Add roster NPC / monster', 'People'], ['orders', 'Extra orders', 'World'], ['soil', 'Soil editor', 'World'], ['trophies', 'Trophy records', 'World'],
  ['player-name', 'Player name', 'System'], ['system', 'System save unlocks', 'System'],
  ['story', 'Story jump planner', 'Expert'], ['flags', 'Expert: story flags', 'Expert'],
  ['raw', 'Expert: raw save fields', 'Expert'], ['reference', 'Read-only item reference', 'Expert'],
  ['review', 'Review & export', 'Save'], ['backups', 'Backups & rollback', 'Save'],
].map(([id, title, group]) => ({ id, title, group }));

function name(kind, id, fallback, lang) {
  return languages[lang]?.[kind]?.[id] || languages.en?.[kind]?.[id] || fallback || `${kind} #${id}`;
}
function person(id, lang) { return name('people', id, constants.people[id] || `NPC ${id}`, lang); }
function item(id, lang) { return id ? name('items', id, itemNames.get(id) || `Item ${id}`, lang) : 'Empty'; }
let itemNames = new Map();
function initialize(data) {
  call('references', data);
  languages = data.languages?.languages || {};
  icons = data.icons || {};
  itemNames = new Map(call('items').map(i => [i.id, i.name]));
  return true;
}
function inventoryOptions(lang, max = Infinity, inherited = false) {
  return [choice('None · 0', 0), ...call('items', { editableOnly: true })
    .filter(i => i.id <= max && (!inherited || [15,16,17,18,19,24,25,26,27,28,29,30,31,32,33,34,35,36,37].includes(i.category)))
    .map(i => choice(`${item(i.id, lang)} · ${i.id}`, i.id))];
}
const selectField = (key, label, options, rest = {}) => field(key, label, 'choice', { options, ...rest });
const seasons = () => constants.seasons.map((n, i) => choice(n, i));

function page(a) {
  const { page: key, language: lang = 'en' } = a;
  const state = call('state');
  const result = { fields: [], values: {}, records: [], selectors: [], info: '', note: '', ready: !!state };
  if (['overview', 'review', 'backups', 'reference', 'gear'].includes(key)) return result;
  const system = ['player-name', 'system'].includes(key);
  if (!state || (key !== 'raw' && state.kind !== (system ? 'system' : 'slot'))) {
    return { ...result, ready: false, note: system ? 'Open rf4_sys.sav to edit these records.' : 'Open a slot save first.' };
  }
  const selector = (key, label, options, value) => result.selectors.push({ key, label, options, value });
  const record = entries => {
    result.records = entries;
    const selected = entries.find(r => String(r.value) === String(a.record)) || entries[0];
    result.record = selected ? String(selected.value) : '';
    result.ready = !!selected;
    return selected?.data;
  };
  const records = (rows, value, label) => record(rows.map(r => ({ ...choice(label(r), value(r)), data: r })));
  let r;
  switch (key) {
    case 'calendar':
      result.fields = [field('day', 'Day', 'number', { min: 1, max: 30 }), selectField('season', 'Season', seasons()), field('year', 'Year', 'number', { min: 1, max: 4294967295 })];
      result.values = state.calendar;
      result.note = 'Direct date changes do not simulate daily game updates.'; break;
    case 'player': result.fields = objectFields(constants.player); result.values = call('player');
      result.note = 'Base values only; equipment-adjusted attributes are not recalculated.'; break;
    case 'inventory': {
      const container = a.container || 'bag';
      selector('container', 'Storage', Object.entries(constants.inventories).map(([k, v]) => choice(v.label, k)), container);
      const rows = call('inventory', { container });
      result.tiles = rows.map(i => ({ ...i, name: item(i.id, lang), icon: icons.items?.[i.id] || '' }));
      const slot = rows.some(i => String(i.slot) === String(a.record)) ? Number(a.record) : 0;
      result.record = String(slot);
      r = call('item', { container, slot });
      const items = inventoryOptions(lang), attachments = items.filter(o => o.value <= 1023), inherited = inventoryOptions(lang, 1023, true);
      result.optionSets = { items, attachments, inherited };
      result.fields = [selectField('id', 'Item (type to search)', items), field('quantity', 'Quantity'),
        field('level', 'Set all item levels', 'number', { optional: true }),
        selectField('element', 'Weapon / tool element', [choice('Keep existing', null), ...constants.elements.map(e => choice(e.name, e.value))]),
        selectField('inherited', 'Inherited equipment', inherited),
        field('totalLevel', 'Total-level bonus (0–150)'), field('rarityBonus', 'Rarity bonus (0–200)'),
        ...Array.from({ length: 3 }, (_, i) => selectField(`craft${i}`, `Crafting attachment ${i + 1}`, attachments)),
        ...Array.from({ length: 9 }, (_, i) => selectField(`upgrade${i}`, `Upgrade ${i + 1} · level ${i + 2}`, attachments))];
      result.values = { id: r.id, quantity: r.quantity, level: null, element: null, ...r.details };
      result.info = `Saved slot ${slot + 1} · ${item(r.id, lang)} · Lv ${r.level}`;
      result.note = 'Saved slots do not unlock capacity. Blank level preserves mixed unit levels. Element changes append crystals without deleting existing upgrades.';
      break;
    }
    case 'skills':
      r = records(call('skills'), r => r.id, r => `${name('skills', r.id, r.name, lang)} · Lv ${r.level}`);
      result.fields = [field('level', 'Skill level'), field('xp', 'Experience (0–16,777,215)')];
      result.values = r; result.note = 'Direct skill levels do not award stat gains. Crafting / resistance skills cap at 99; others at 999.'; break;
    case 'friendship':
      r = records(call('friendship'), r => r.id, r => `${person(r.id, lang)} · Lv ${r.level}`);
      result.fields = [field('level', 'Friendship level (0–10,000)')]; result.values = r;
      result.note = 'Does not trigger dating, wedding or story events.'; break;
    case 'relationships': {
      r = records(call('relationships'), r => r.id, r => person(r.id, lang));
      const nicknames = languages[lang]?.nicknames || languages.en?.nicknames || [];
      const nickChoices = key => {
        const opts = new Map();
        for (const gender of ['male', 'female']) opts.set(r.defaults[gender][key], `Default for ${gender === 'male' ? 'Lest' : 'Frey'}`);
        nicknames.slice(0, constants.nicknameCount).forEach((n, i) => { if (n && !opts.has(i)) opts.set(i, n.replaceAll('＠しゅじんこうくん＠', '[Player name]')); });
        if (!opts.has(r[key])) opts.set(r[key], 'Stored nickname · keep unless verified');
        return [...opts].map(([id, n]) => choice(`${n} · #${id}`, id));
      };
      result.fields = [bool('experimental', 'Experimental non-candidate flags (no romance scripts added)'), bool('dating', 'Saved dating status'),
        selectField('npcCallsPlayer', 'NPC calls player', nickChoices('npcCallsPlayer')), selectField('playerCallsNpc', 'Player calls NPC', nickChoices('playerCallsNpc'))];
      result.values = { ...r, experimental: false };
      result.note = 'Saved flags and nicknames only; does not simulate confessions, breakups, marriage or story events.'; break;
    }
    case 'people': case 'monsters': {
      const monster = key === 'monsters';
      r = records(monster ? call('monsters') : Array.from({ length: 26 }, (_, i) => ({ id: i + 1 })), r => r.id,
        r => monster ? `${r.id + 1} · ${r.name || 'Unnamed'} · species ${r.species}` : person(r.id, lang));
      result.fields = [...(monster ? [field('friendship', 'Friendship (0–1,000)')] : []), ...objectFields(constants.stats)];
      if (r) result.values = { ...call('stats', { kind: monster ? 'monster' : 'person', id: r.id }), ...(monster ? { friendship: r.friendship } : {}) };
      result.note = 'Stored base stats only; names, species and barns are preserved.'; break;
    }
    case 'recipes': {
      const group = a.group || 'all';
      selector('group', 'Recipe group', [choice('All groups', 'all'), ...Object.entries(constants.recipeGroups).map(([k, n]) => choice(n, k))], group);
      const rows = call('recipes').filter(r => group === 'all' || r.kind === group);
      r = records(rows, r => `${r.kind}:${r.index}`, r => `${item(r.result, lang)} · difficulty ${r.level} · variant ${r.index}`);
      result.fields = [bool('known', 'Recipe learned')]; result.values = r;
      result.note = 'Variants sharing a learned bit change together. Recipe difficulty is not editable.'; break;
    }
    case 'trophies':
      r = records(call('trophies'), r => r.name, r => r.label);
      result.fields = [selectField('value', 'Recorded result', (r.width === 1 ? ['Not recorded', 'Recorded'] : ['None', 'Gold / first', 'Silver / second', 'Bronze / third']).map((n, i) => choice(n, i)))];
      result.values = r; result.note = 'Recorded game results only, not physical trophies or Steam achievements.'; break;
    case 'orders': {
      const c = call('orderConstants'), group = a.group || 'effects';
      selector('group', 'Order group', c.groups.map(g => choice(g.name, g.id)), group);
      result.fields = c.fields.filter(f => f.group === group).map(f => ({ ...f,
        options: f.key === 'appearance' ? c.appearances.map(v => choice(v.name || person(v.id, lang), v.id)) :
          f.key === 'bgm' ? c.bgm.map(v => choice(v.name, v.id)) : f.key === 'morningCaller' ? c.morningCallers.map(v => choice(v.name || person(v.id, lang), v.id)) : undefined }));
      result.values = call('orders');
      result.note = 'Unlock flags do not deliver furniture, build facilities or run order scripts. Rank and expansion levels are raw stored values, not verified gameplay caps. Do not shrink occupied storage.'; break;
    }
    case 'soil': {
      const c = call('soilConstants'), farm = Number(a.farm || 0), patches = c.farms[farm].patches;
      const patch = patches.includes(Number(a.patch)) ? Number(a.patch) : patches[0];
      selector('farm', 'Field', c.farms.map(f => choice(f.name, f.id)), farm);
      selector('patch', 'Soil patch', patches.map(i => choice(`Soil patch ${i + 1}`, i)), patch);
      result.fields = [bool('all', 'Apply changed fields to every used patch on this field'), ...c.fields.map(f => ({ ...f, kind: f.width === 1 ? 'bool' : 'number' }))];
      result.values = { ...call('soil', { farm, patch }).values, all: false };
      result.note = 'Raw packed soil values, not crop growth or a magnifying-glass simulator. Crop records and unused patches are preserved.'; break;
    }
    case 'marriage': {
      r = records(constants.candidates, r => r.id, r => person(r.id, lang));
      result.fields = [bool('experimental', 'Experimental non-candidate flags (no romance scripts added)'), ...constants.marriage.map(f => ({ ...f,
        kind: ['spouse', 'season'].includes(f.key) ? 'choice' : f.max === 1 ? 'bool' : 'number',
        options: f.key === 'season' ? seasons() : f.key === 'spouse' ? [choice('None · 0', 0), ...Array.from({ length: 31 }, (_, i) => choice(`${person(i + 1, lang)} · ${i + 1}`, i + 1))] : undefined })),
        bool('marriageEvent', 'Candidate marriage event cleared'), bool('newlywedEvent', 'Candidate newlywed event cleared')];
      result.values = { ...call('marriage', { candidate: r.id }), experimental: false };
      result.note = 'Flags only, not a complete marry/divorce operation. Non-candidates have no wedding/romance scripts. Pregnancy, children and schedules are not simulated.'; break;
    }
    case 'roster': {
      const data = call('roster'), free = data.slots.filter(r => !r.occupied), rooms = data.housing.filter(r => r.free > 0);
      result.ready = !!(free.length && rooms.length);
      result.fields = [selectField('species', 'NPC / monster species (1–255; not all IDs are valid actors)', Array.from({ length: 255 }, (_, i) => choice(`${i + 1} · ${person(i + 1, lang)}`, i + 1))),
        field('name', 'Roster name (up to 6 characters / 18 UTF-8 bytes)', 'text'),
        selectField('slot', 'Empty destination slot', free.map(r => choice(`${r.id + 1} (ID ${r.id})`, r.id))),
        selectField('room', 'Built barn room', rooms.map(r => choice(`Barn ${r.barn + 1} / Room ${r.room + 1} · ${r.free}/4`, r.map))),
        field('friendship', 'Friendship (0–1,000)'), selectField('sourceKind', 'Stat source', choices([['Basic level 1', 'basic'], ['Existing monster stats', 'monster'], ['Existing NPC stats', 'person']])),
        field('sourceId', 'Source ID (NPC 1–26 / monster slot 0–199)'), bool('acknowledgeRisk', 'I accept experimental roster compatibility risks')];
      result.values = { species: 48, name: '', slot: free[0]?.id, room: rooms[0]?.map, friendship: 0, sourceKind: 'basic', sourceId: 0, acknowledgeRisk: false };
      result.info = `${200 - free.length}/200 · Free barn places: ${rooms.reduce((n, r) => n + r.free, 0)}`;
      result.note = 'Experimental: writes an empty tamed-monster slot, not the town NPC. NPC species may fail to spawn or lack monster AI, riding and produce. Requires a built barn room with space.'; break;
    }
    case 'system':
      result.fields = constants.systemFlags.map(f => bool(String(f.bit), f.label));
      result.values = Object.fromEntries(call('system').map(f => [f.bit, f.value]));
      result.note = 'Persistent ending/wedding/data-transfer records only. These do not simulate events or advance slot saves.'; break;
    case 'player-name':
      r = records(call('playerNames'), r => r.id, r => `Bank ${r.bank + 1} · slot ${String(r.slot).padStart(2, '0')} · ${r.present ? r.name || '[Game default]' : '[Empty slot]'}`);
      result.ready = r.present;
      result.fields = [field('name', 'Player name (up to 6 characters / 18 UTF-8 bytes)', 'text')]; result.values = { name: r.name };
      result.note = 'Names are stored in rf4_sys.sav, not individual slot files. Blank uses the game default. Editing a name does not create a slot.'; break;
    case 'flags': {
      const rows = call('flags');
      const group = a.group || 'all';
      selector('group', 'Flag group', [choice('All flags', 'all'), ...[...new Set(rows.map(r => r.group))].sort().map(g => choice(g, g))], group);
      r = records(rows.filter(r => group === 'all' || r.group === group), r => r.name, r => `${r.help.title[lang === 'zh-CN' ? 'zh' : 'en']} · ${r.name}`);
      if (r) { result.fields = [field('value', `Value (0–${2 ** r.width - 1})`)]; result.values = { value: r.value };
        result.info = `Bit ${r.bitOffset} · ${r.width} bits\n${r.help.original}\n${r.help.evidence}\n${r.help.impact[lang === 'zh-CN' ? 'zh' : 'en']}`; }
      result.note = 'Story changes can break progression. These controls do not initialize world state, reward quests or replay events.'; break;
    }
    case 'story': {
      const main = call('flags').find(f => f.name === 'REG_MAIN_SCENARIO');
      result.fields = [field('target', 'Target story stage (0–511)', 'number', { min: 0, max: 511 }),
        field('flags', 'Explicit supporting flags (JSON object; blank keeps other flags)', 'text'),
        bool('acknowledgeRisk', 'I understand this does not reconstruct a playable checkpoint'), bool('allowRewind', 'Allow rewind (later world state is not reverted)')];
      result.values = { target: main.value, flags: '', acknowledgeRisk: false, allowRewind: false };
      selector('witness', 'Script witness (not a playable preset)', [choice('Choose a script witness', ''), ...constants.storyWitnesses.map(w => choice(`${w.value} · ${w[lang === 'zh-CN' ? 'zh' : 'en']}`, w.value))], '');
      result.note = 'Story jumps do not reconstruct a playable checkpoint, run event cleanup or synthesize world records. Review the preview before acknowledging risk.'; break;
    }
    case 'raw':
      result.fields = [field('offset', 'File offset (decimal or 0x hex)'), selectField('type', 'Integer type', ['u8','i8','u16','i16','u32','i32'].map(n => choice(n, n))),
        field('value', 'New integer value', 'number', { optional: true }), field('bytes', 'OR hex bytes to patch', 'text')];
      result.values = { offset: state.kind === 'system' ? 8 : 20, type: 'u32', value: null, bytes: '' };
      result.note = 'Use only independently verified offsets. The checksum header is protected; raw edits may break the save. Enter either an integer or at most 256 hex bytes.'; break;
    default: throw new Error('Unknown editor page.');
  }
  result.values ||= {};
  // Preserve unknown stored enum values instead of silently choosing the first.
  for (const f of result.fields) if (f.kind === 'choice') {
    const v = result.values[f.key];
    if (v !== undefined && !f.options.some(o => o.value === v)) f.options.push(choice(`Stored value ${v} · keep unless verified`, v));
  }
  for (const f of result.fields) for (const [key, options] of Object.entries(result.optionSets || {})) {
    if (f.options === options) { f.optionsRef = key; delete f.options; break; }
  }
  return result;
}

function operations(a) {
  const { page: key, values: v, record } = a;
  // The save API intentionally rejects booleans as integer fields. Keep actual
  // consent switches boolean, but encode saved one-bit fields as 0/1.
  const c = Object.fromEntries(Object.entries(a.changes).map(([k, v]) => [k, typeof v === 'boolean' ? Number(v) : v]));
  const id = Number(record), op = (operation, args) => [{ operation, args }];
  switch (key) {
    case 'calendar': return op('setCalendar', { changes: { ...v, ...c } });
    case 'player': return op('setPlayer', { changes: c });
    case 'inventory': {
      const changes = { id: v.id, quantity: v.quantity };
      if (c.level != null) changes.level = c.level;
      const details = Object.fromEntries(Object.entries(c).filter(([k, v]) => !['id','quantity','level'].includes(k) && v != null));
      return op('setItem', { container: a.container || 'bag', slot: id, changes, details });
    }
    case 'skills': return op('setSkill', { id, changes: c });
    case 'friendship': return op('setFriendship', { id, level: c.level });
    case 'relationships': return op('setRelationship', { id, changes: { ...c, experimental: !!v.experimental } });
    case 'people': return op('setStats', { kind: 'person', id, changes: c });
    case 'monsters': return op('setMonster', { id, changes: { ...(c.friendship == null ? {} : { friendship: c.friendship }), stats: Object.fromEntries(Object.entries(c).filter(([k]) => k !== 'friendship')) } });
    case 'recipes': return op('setRecipes', { recipes: call('recipes').filter(r => `${r.kind}:${r.index}` === record), known: !!c.known });
    case 'trophies': return op('setTrophy', { name: record, value: c.value });
    case 'orders': return op('setOrders', { changes: c });
    case 'soil': return op('setSoil', { farm: Number(a.farm || 0), patch: Number(a.patch || 0), all: !!v.all, changes: Object.fromEntries(Object.entries(c).filter(([k]) => k !== 'all')) });
    case 'marriage': return op('setMarriage', { candidate: id, changes: { ...c, experimental: !!v.experimental } });
    case 'roster': return op('setRosterAdd', v);
    case 'system': return op('setSystem', { changes: c });
    case 'player-name': return op('setPlayerName', { id, name: v.name });
    case 'flags': return op('setFlag', { name: record, value: c.value });
    case 'story': return op('setStoryJump', storyOptions(v));
    case 'raw':
      if ((v.value != null) === !!v.bytes.trim()) throw new Error('Enter either an integer or hex bytes.');
      return v.bytes.trim() ? op('patchBytes', { offset: v.offset, text: v.bytes }) : op('setNumber', { offset: v.offset, type: v.type, value: v.value });
    default: throw new Error('This page has no editable form.');
  }
}
function storyOptions(v) { return { ...v, flags: v.flags.trim() ? JSON.parse(v.flags) : {} }; }

export function invoke(operation, a = {}) {
  switch (operation) {
    case 'initialize': return initialize(a);
    case 'importLanguages': {
      const staged = { ...languages };
      for (const file of a.files) {
        const match = /^rf3TxtHeroNickName\.(eng|jpn|fra|deu|kor|twn|chn)$/i.exec(file.name);
        const table = match ? { ...GAME_LANGUAGES[match[1].toLowerCase()], kind: 'nicknames', names: parseGameText(file.bytes) } : languageTable(file.name, file.bytes);
        staged[table.code] = { ...staged[table.code], label: table.label, [table.kind]: table.names };
      }
      languages = staged; return true;
    }
    case 'importItems': {
      const result = call(operation, a); itemNames = new Map(call('items').map(i => [i.id, i.name])); return result;
    }
    case 'navigation': return pages;
    case 'languages': return [choice('English', 'en'), ...Object.entries(languages).filter(([k]) => k !== 'en').map(([k, v]) => choice(v.label, k))];
    case 'page': return page(a);
    case 'operations': return operations(a);
    case 'storyPreview': return call('storyJumpPreview', { ...storyOptions(a.values), language: a.language === 'zh-CN' ? 'zh' : 'en' }).explanation;
    case 'gearPreview': {
      const preset = call('gearPreset', a);
      return preset.items.map(i => `${i.role}: ${item(i.id, a.language)} · #${i.id}\nCrafting attachments: ${i.craft.map(m => item(m.id, a.language)).join(', ')}\nUpgrades in order: ${i.upgrades.map(m => item(m.id, a.language)).join(' → ')}`).join('\n\n');
    }
    case 'itemPreview': {
      const op = operations({ ...a, page: 'inventory' })[0];
      const preview = call('previewItem', { ...op.args });
      for (const view of [preview.before, preview.after]) {
        view.item.name = item(view.item.id, a.language);
        for (const section of view.sections) section.name = item(section.id, a.language);
      }
      return preview;
    }
    case 'learnRecipes': {
      const rows = call('recipes').filter(r => a.all || ((!a.group || a.group === 'all' || r.kind === a.group) && (!a.query || `${item(r.result, a.language)} · difficulty ${r.level} · variant ${r.index} ${r.kind}:${r.index}`.toLowerCase().includes(a.query.toLowerCase()))));
      if (!rows.length) throw new Error('No recipes match the current filters.');
      return call('applyOperations', { operations: [...(a.operations || []), { operation: 'setRecipes', args: { recipes: rows, known: a.known } }] });
    }
    default: return call(operation, a);
  }
}
export function invokeJSON(operation, text) { return JSON.stringify(invoke(operation, JSON.parse(text))); }
