import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, STORY_REGISTER } from '../web/save-core.js';
import { SoilEditor, SOIL_FIELDS, SOIL_FARMS, SOIL_OFFSET } from '../web/soil-core.js';
import { RosterEditor } from '../web/roster-core.js';
import { ExtendedSave, MONSTER_OFFSET } from '../web/extended-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';
import { RelationshipEditor } from '../web/relationship-core.js';
import { MarriageEditor } from '../web/marriage-core.js';
import { ProgressCatalog } from '../web/progress-core.js';
import { ENDGAME_SHORTCUT, previewStoryJump, applyStoryJump } from '../web/story-jump.js';
import { nativeInvoke as call } from '../web/native-core.js';

const field = name => SAVE_METADATA.symbols.find(field => field.name === name);
function fixture(platform = 'pc') {
  const seed = createDemo(); seed.setFlag(field('REG_MON_HOUSE0_L_LV'), 1);
  return new SaveDocument(seed.build({ platform, experimental: true }));
}

test('soil packed edits preserve every non-target bit, crops and unused patches', () => {
  for (const farm of SOIL_FARMS) for (const patch of farm.patches) {
    const save = createDemo(), soil = new SoilEditor(save);
    save.data.fill(0xa5, SOIL_OFFSET, SOIL_OFFSET + 9 * 18 * 16);
    const before = save.data.slice(), base = soil.values(farm.id, patch).offset;
    const changes = Object.fromEntries(SOIL_FIELDS.map(field => [field.key, field.max]));
    const allowed = new Set(SOIL_FIELDS.flatMap(field => Array.from({ length: field.width }, (_, i) => (base * 8) + field.bit + i)));
    soil.apply(farm.id, patch, changes);
    assert.deepEqual(soil.values(farm.id, patch).values, changes);
    for (let offset = 0; offset < save.size; offset++) if (save.data[offset] !== before[offset]) {
      for (let bit = 0; bit < 8; bit++) if (!allowed.has(offset * 8 + bit)) assert.equal(save.data[offset] >> bit & 1, before[offset] >> bit & 1);
    }
    assert.equal(save.undoStack.length, 1);
    save.undo(); assert.deepEqual(save.data, before);
    save.redo(); assert.deepEqual(soil.values(farm.id, patch).values, changes);
  }
});

test('soil selected-field bulk changes touch only requested bits in used patches', () => {
  for (const platform of ['pc', 'switch']) {
    const save = fixture(platform), soil = new SoilEditor(save), before = save.data.slice();
    soil.apply(7, 0, { health: 255 }, true);
    const allowed = new Set(SOIL_FARMS[7].patches.map(patch => SOIL_OFFSET + (7 * 18 + patch) * 16 + 6));
    for (let offset = 0; offset < save.size; offset++) assert.equal(save.data[offset], allowed.has(offset) ? 255 : before[offset]);
    assert.equal(save.undoStack.length, 1); assert.equal(new SaveDocument(save.build()).crcValid, true);
    save.undo(); assert.deepEqual(save.data, before);
  }
});

test('soil rejects bad indexes, unknown fields and a bad final value atomically', () => {
  const save = createDemo(), soil = new SoilEditor(save);
  for (const args of [[9,0,{health:1}], [7,2,{health:1}], [0,18,{health:1}], [0,0,{crop:1}], [0,0,{health:255,defense:64}], [0,0,{health:''}], [0,0,{health:2},1]]) {
    assert.throws(() => soil.apply(...args)); assert.deepEqual(save.data, save.original); assert.equal(save.undoStack.length, 0);
  }
});

test('experimental dating edits all 23 main records but never invents guest fields', () => {
  for (let id = 1; id <= 23; id++) {
    const save = createDemo(), editor = new RelationshipEditor(save), before = save.data.slice();
    if (!editor.values(id).canDate) assert.throws(() => editor.apply(id, { dating: 1 }));
    editor.apply(id, { dating: 1 }, { experimental: true });
    const expected = before.slice(); expected[0x1db40 + (id - 1) * 44 + 10] |= 0x40;
    assert.deepEqual(save.data, expected); assert.equal(editor.values(id).dating, 1);
    assert.equal(save.undoStack.length, 1); save.undo(); assert.deepEqual(save.data, before);
  }
  for (const id of [0, 24, 25, 26, 256]) assert.throws(() => new RelationshipEditor(createDemo()).apply(id, { dating: 1 }, { experimental: true }));
});

test('experimental spouse supports the entire five-bit ID range without candidate event fabrication', () => {
  for (let id = 1; id <= 31; id++) {
    const save = createDemo(), editor = new MarriageEditor(save), before = save.data.slice();
    editor.apply({ spouse: id }, 1, { experimental: true });
    assert.equal(editor.values().spouse, id);
    assert.deepEqual(editor.events(1), { marriageEvent: 0, newlywedEvent: 0 });
    for (let offset = 0; offset < save.size; offset++) if (save.data[offset] !== before[offset]) assert.ok(offset >= 0x1e8c4 && offset < 0x1e8c4 + 832);
    assert.equal(new SaveDocument(save.build()).crcValid, true); save.undo(); assert.deepEqual(save.data, before);
  }
  assert.throws(() => new MarriageEditor(createDemo()).apply({ spouse: 32 }, 1, { experimental: true }));
});

for (const platform of ['pc', 'switch']) test(`${platform}: new roster NPC/monster writes exactly one roster and full stat block`, () => {
  for (const species of [3, 21, 24, 48, 110, 252, 255]) {
    const save = fixture(platform), editor = new RosterEditor(save), before = save.data.slice();
    editor.add({ species, name: '芙蕾A', friendship: 10, acknowledgeRisk: true });
    const monster = new ExtendedSave(save).monster(0);
    assert.equal(monster.species, species); assert.equal(monster.name, '芙蕾A'); assert.equal(monster.barn, 77); assert.equal(monster.friendship, 10); assert.equal(monster.occupied, true);
    assert.equal(save.data[MONSTER_OFFSET + 19], 0); assert.equal(save.readNumber(MONSTER_OFFSET + 22, 'u16'), 77);
    assert.equal(monster.flags, 0x1000);
    assert.equal(new ExtendedSave(save).stats('monster', 0).level, 1);
    for (let offset = 0; offset < save.size; offset++) if (save.data[offset] !== before[offset]) assert.ok(offset >= MONSTER_OFFSET && offset < MONSTER_OFFSET + 36 || offset >= 0xb44 && offset < 0xb44 + 100);
    assert.equal(save.undoStack.length, 1); assert.equal(new SaveDocument(save.build()).crcValid, true);
    const after = save.data.slice(); save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.deepEqual(save.data, after);
  }
});

test('roster allocation enforces four per built room and never overwrites a monster', () => {
  const save = fixture(), editor = new RosterEditor(save);
  for (let slot = 0; slot < 4; slot++) editor.add({ species: 48 + slot, acknowledgeRisk: true });
  const before = save.data.slice(), count = save.undoStack.length;
  assert.equal(editor.housing()[0].free, 0);
  assert.throws(() => editor.add({ species: 100, acknowledgeRisk: true }), /barn room/);
  assert.throws(() => editor.add({ species: 100, slot: 0, acknowledgeRisk: true }), /empty/);
  assert.deepEqual(save.data, before); assert.equal(save.undoStack.length, count);
  const noBarn = createDemo(); assert.throws(() => new RosterEditor(noBarn).add({ species: 110, acknowledgeRisk: true }), /barn room/);
});

test('roster templates copy a complete saved stat record, not transient roster identity', () => {
  const save = fixture(), editor = new RosterEditor(save);
  editor.add({ species: 110, friendship: 10, stats: { level: 50, max_hp: 500, hp: 450 }, acknowledgeRisk: true });
  const source = save.data.slice(0xb44, 0xb44 + 100);
  editor.add({ species: 21, sourceKind: 'monster', sourceId: 0, acknowledgeRisk: true });
  assert.deepEqual(save.data.slice(0xb44 + 100, 0xb44 + 200), source);
  assert.equal(save.data[MONSTER_OFFSET + 36 + 19], 1);
  assert.equal(new ExtendedSave(save).monster(1).friendship, 0);
  const before = save.data.slice();
  for (const options of [{ species: 0 }, { species: 256 }, { species: 48, name: '1234567' }, { species: 48, sourceKind: 'monster', sourceId: 199 }, { species: 48, stats: { max_hp: 5, hp: 6 } }, { species: 48, room: 78 }, { species: 48, friendship: 1001 }, { species: 48, sourceKind: 'unknown' }]) {
    assert.throws(() => editor.add({ ...options, acknowledgeRisk: true })); assert.deepEqual(save.data, before);
  }
  assert.throws(() => editor.add({ species: 48 }));
});

test('endgame shortcut is staged/read-only until acknowledged and writes only its explicit three flags', () => {
  const save = createDemo(), catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
  save.setFlag(field('FLG_SYELZA_ERACE'), 1); save.setFlag(field('FLG_SYELZA_SUBEV_STOP'), 1);
  const before = save.data.slice(), depth = save.undoStack.length;
  const plan = previewStoryJump(save, catalog, ENDGAME_SHORTCUT);
  assert.equal(plan.target, 511); assert.equal(plan.fields.length, 3); assert.equal(plan.playableCheckpoint, 'unverified');
  assert.deepEqual(save.data, before); assert.throws(() => applyStoryJump(save, catalog, ENDGAME_SHORTCUT));
  applyStoryJump(save, catalog, { ...ENDGAME_SHORTCUT, acknowledgeRisk: true });
  assert.equal(save.flag(STORY_REGISTER), 511); assert.equal(save.flag(field('FLG_SYELZA_ERACE')), 0);
  assert.equal(save.undoStack.length, depth + 1); save.undo(); assert.deepEqual(save.data, before);
});

test('native mixed edit batch handles new editors and rolls back a failing roster addition', () => {
  const save = fixture(); call('open', { bytes: Array.from(save.original), name: 'synthetic.sav' });
  const original = call('working');
  const ops = [{ operation: 'setSoil', args: { farm: 0, patch: 0, changes: { health: 255 }, all: true } }, { operation: 'setRelationship', args: { id: 3, changes: { dating: 1, experimental: true } } }, { operation: 'setMarriage', args: { candidate: 1, changes: { spouse: 21, experimental: true } } }, { operation: 'setRosterAdd', args: { species: 3, acknowledgeRisk: true } }];
  assert.throws(() => call('applyOperations', { operations: [...ops, { operation: 'setRosterAdd', args: { species: 48, slot: 0, acknowledgeRisk: true } }] }));
  assert.deepEqual(call('working'), original); assert.equal(call('state').undo, 0);
  call('applyOperations', { operations: ops });
  assert.equal(call('state').undo, 1); assert.equal(call('monsters').length, 1);
  call('undo'); assert.deepEqual(call('working'), original);
});
