import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo } from '../web/save-core.js';
import { ItemCatalog } from '../web/game-reference.js';
import { referenceEffects, previewItemEdit } from '../web/item-effects.js';

function catalog() {
  const items = Array.from({ length: 1024 }, () => ({ category: 51, max_stack: 9 }));
  items[328] = { category: 15, max_stack: 1 };
  items[559] = { category: 33, max_stack: 1 };
  const equipment = Array.from({ length: 1024 }, () => ({ gear_params: 0 }));
  equipment[328] = { gear_params: 2, attack: 5, crit: 4096 };
  equipment[559] = { gear_params: 0, acc_params: 0x40000, defense: 10 };
  const upgrades = Array.from({ length: 1024 }, () => ({}));
  upgrades[839] = { defense: 3, fire_res: -2048 };
  return new ItemCatalog({ tables: { item: { count: 1024, records: items }, equipment: { count: 1024, records: equipment }, upgrade: { count: 1024, records: upgrades } } });
}

test('effect references decode fixed-point percentages, duration and unknown flags without inventing final stats', () => {
  const effects = referenceEffects('use', { hp: 30, hp_pct: 4096, poison_res: -2048, effect_duration: 4, level_scaling: 4096, status_flags: 0x80000001 });
  assert.equal(effects.find(effect => effect.field === 'hp').value, 30);
  assert.equal(effects.find(effect => effect.field === 'hp_pct').value, 100);
  assert.equal(effects.find(effect => effect.field === 'poison_res').value, -50);
  assert.equal(effects.find(effect => effect.field === 'effect_duration').value, 12);
  assert.equal(effects.find(effect => effect.field === 'level_scaling').value, 12.5);
  assert.ok(effects.some(effect => effect.label === 'HealPoison'));
  assert.ok(effects.some(effect => effect.kind === 'unknown' && effect.raw === 0x80000000));
  assert.deepEqual(referenceEffects('upgrade', null), []);
});

test('draft item preview uses the real edit algorithm and preserves source, undo and redo', () => {
  const save = createDemo(), cat = catalog();
  save.setPlayer({ money: 500 }); save.undo();
  const bytes = save.data.slice(), undo = save.undoStack.slice(), redo = save.redoStack.slice();
  const preview = previewItemEdit(save, 'bag', 0, { id: 328, quantity: 1 }, { craft0: 839, inherited: 559, element: 1 }, cat);
  assert.equal(preview.changed, true);
  assert.equal(preview.before.item.element, 2);
  assert.equal(preview.after.item.element, 1);
  assert.equal(preview.after.exactFinalStats, false);
  assert.equal(preview.after.sections.find(section => section.role === 'craft').effects.find(effect => effect.field === 'defense').value, 3);
  assert.ok(preview.after.sections.some(section => section.title === 'Inherited equipment parameters'));
  assert.ok(preview.after.notices.some(note => note.includes('Not simulated')));
  assert.deepEqual(save.data, bytes); assert.deepEqual(save.undoStack, undo); assert.deepEqual(save.redoStack, redo);
});

test('missing references are unavailable, never fabricated as zero bonuses', () => {
  const save = createDemo(), cat = catalog();
  delete cat.local.tables.equipment;
  const result = previewItemEdit(save, 'bag', 0, {}, {}, cat);
  assert.equal(result.after.item.element, null);
  assert.equal(result.after.sections[0].available, false);
  assert.ok(result.after.notices.some(note => note.includes('Read your game')));
});

test('clear/replacement and invalid drafts obey the same guards as an actual edit', () => {
  const save = createDemo(), cat = catalog(), before = save.data.slice();
  const cleared = previewItemEdit(save, 'bag', 0, { id: 0, quantity: 0 }, {}, cat);
  assert.equal(cleared.after.item.id, 0); assert.deepEqual(cleared.after.sections, []);
  assert.throws(() => previewItemEdit(save, 'bag', 0, { quantity: '' }, {}, cat));
  assert.throws(() => previewItemEdit(save, 'bag', 0, {}, { upgrade0: 1024 }, cat));
  assert.deepEqual(save.data, before);
});
