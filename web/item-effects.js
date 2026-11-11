// Read-only preview of definitions; final game stats are not calculated.
import { SaveDocument, equalBytes } from './save-core.js';
import { VENTI_TABLES } from './game-schema.js';
import { editInventoryItem, itemDetails, equipmentItem, equipmentElement } from './item-details.js';

const LABELS = {
  attack: 'ATK', magic_attack: 'M.ATK', defense: 'DEF', magic_defense: 'M.DEF',
  strength: 'STR', intelligence: 'INT', vitality: 'VIT', dizzy: 'Dizzy',
  crit: 'Critical chance', knock: 'Knockback', stun: 'Stun duration',
  hp: 'HP recovery', rp: 'RP recovery', hp_pct: 'HP recovery', rp_pct: 'RP recovery',
  max_hp: 'Max HP', max_rp: 'Max RP', perm_hp: 'Permanent HP',
  perm_strength: 'Permanent STR', perm_intelligence: 'Permanent INT', perm_vitality: 'Permanent VIT',
  effect_duration: 'Effect duration', level_scaling: 'Per-level scaling reference',
  hit_range: 'Attack range', hit_arc: 'Attack arc', difficulty: 'Upgrade difficulty',
};
const STATUS = { poison: 'Poison', seal: 'Seal', paralysis: 'Paralysis', sleep: 'Sleep', fatigue: 'Fatigue', sick: 'Sick', faint: 'Instant death', drain: 'HP drain', fire: 'Fire', water: 'Water', earth: 'Earth', wind: 'Wind', light: 'Light', dark: 'Dark', love: 'Love', physical: 'Physical', dizzy: 'Dizzy', crit: 'Critical', knock: 'Knockback' };
const OMIT = new Set(['model', 'depth']); // model is not an effect; depth meaning is ambiguous.

function fieldLabel(field) {
  if (LABELS[field]) return LABELS[field];
  if (field.endsWith('_cook')) return `${fieldLabel(field.slice(0, -5))} · cooking ingredient`;
  if (field.endsWith('_pct')) return fieldLabel(field.slice(0, -4));
  const match = /^(.*)_(atk|res)$/.exec(field);
  return match ? `${STATUS[match[1]] || match[1]} ${match[2] === 'atk' ? 'infliction / attack' : 'resistance'}` : field;
}

function percentField(field) {
  return field.endsWith('_pct') || /_(atk|res)(?:_cook)?$/.test(field) || ['crit', 'knock', 'stun', 'crit_cook', 'hit_range', 'hit_arc'].includes(field);
}

export function referenceEffects(type, record) {
  if (!record) return [];
  const schema = VENTI_TABLES[type];
  const effects = [];
  for (const [field, spec] of Object.entries(schema.fields)) {
    const raw = record[field];
    if (!Number.isInteger(raw) || raw === 0 || OMIT.has(field) || field.startsWith('unknown_')) continue;
    if (spec.bitmask) {
      let known = 0;
      for (const [label, mask] of Object.entries(spec.enum)) {
        if (!mask) continue;
        known = (known | mask) >>> 0;
        if ((raw & mask) === mask) effects.push({ field, label, raw: mask, value: true, unit: '', kind: 'flag' });
      }
      const unknown = (raw & ~known) >>> 0;
      if (unknown) effects.push({ field, label: 'Unknown bits', raw: unknown, value: `0x${unknown.toString(16).toUpperCase()}`, unit: '', kind: 'unknown' });
      continue;
    }
    const percent = percentField(field);
    effects.push({ field, label: fieldLabel(field), raw, value: field === 'effect_duration' ? raw * 3 : field === 'level_scaling' ? raw * 100 / 32768 : percent ? raw * 100 / 4096 : raw, unit: field === 'effect_duration' ? 'game minutes' : percent || field === 'level_scaling' ? '%' : '', kind: 'number' });
  }
  return effects;
}

function itemPreview(save, container, slot, catalog) {
  const item = save.inventorySlot(container, slot);
  const definition = item.id ? catalog.bagDefinition(item.id) : null;
  const details = itemDetails(save, container, slot);
  const sections = [], notices = [];
  let element = null;
  function section(type, id, title, extra = {}) {
    let record = null;
    try { record = catalog.record(type, id); } catch { /* Missing/out-of-range references stay unknown. */ }
    sections.push({ title, id, type, ...extra, available: Boolean(record), effects: referenceEffects(type, record), source: VENTI_TABLES[type].source });
    if (!record) notices.push('Read your game equipment / use / upgrade tables to preview effects.');
  }
  if (equipmentItem(definition)) {
    section('equipment', item.id, 'Base equipment parameters');
    if (details.inherited) section('equipment', details.inherited, 'Inherited equipment parameters');
    try { element = equipmentElement(item.id, details, catalog); } catch { /* Do not invent an element. */ }
    for (const kind of ['craft', 'upgrade']) for (let index = 0; index < (kind === 'craft' ? 3 : 9); index++) {
      const id = details[`${kind}${index}`];
      if (id) section('upgrade', id, kind === 'craft' ? `Crafting attachment ${index + 1}` : `Upgrade ${index + 1} · level ${index + 2}`, { role: kind, slot: index });
    }
    notices.push('Not simulated: repeated-material penalties, material levels, total-level/rarity bonuses, special upgrade multipliers, inheritance combinations and actor stats.');
  } else if (item.id) {
    section('use', item.id, 'Base use effects');
    section('upgrade', item.id, 'Raw material bonuses');
    notices.push('Item-level scaling and cooking combinations are not simulated.');
  }
  return { item: { id: item.id, quantity: item.quantity, level: item.level, element }, details, sections, notices: [...new Set(notices)], exactFinalStats: false };
}

export function previewItemEdit(save, container, slot, changes, detailChanges, catalog) {
  const before = itemPreview(save, container, slot, catalog);
  const clone = new SaveDocument(save.data);
  const current = clone.inventorySlot(container, slot);
  if (Object.keys(changes || {}).length || Object.keys(detailChanges || {}).length) {
    const staged = { id: current.id, quantity: current.quantity, ...changes };
    editInventoryItem(clone, container, slot, staged, staged.id ? catalog.bagDefinition(staged.id) : null, catalog, detailChanges || {});
  }
  return { before, after: itemPreview(clone, container, slot, catalog), changed: !equalBytes(save.data.subarray(current.offset, current.offset + 28), clone.data.subarray(current.offset, current.offset + 28)), scope: 'Definition-based preview, not final in-game stats.' };
}
