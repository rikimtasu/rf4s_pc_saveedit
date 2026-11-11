import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, BAG_OFFSET, ITEM_RECORD_SIZE } from '../web/save-core.js';
import { OrdersEditor, ORDER_FIELDS } from '../web/orders-core.js';
import { SoilEditor, SOIL_FARMS, SOIL_MAXIMUM, SOIL_FIELDS } from '../web/soil-core.js';
import { ItemCatalog } from '../web/game-reference.js';
import { GEAR_PRESETS, gearPreset, giveGearPreset } from '../web/gear-presets.js';
import { itemDetails } from '../web/item-details.js';
import { nativeInvoke as call } from '../web/native-core.js';

const fixture = platform => new SaveDocument(createDemo().build(platform === 'switch' ? { platform, experimental: true } : {}));
function references() {
  const records = Array.from({ length: 1024 }, () => ({ category: 51, max_stack: 9 }));
  for (const [id, category] of [[501, 24], [595, 33], [749, 37], [706, 35], [729, 36], [665, 34], [626, 34], [662, 34], [661, 34], [674, 34], [725, 36], [719, 36], [723, 36], [567, 28]]) records[id] = { category, max_stack: 1 };
  const equipment = Array.from({ length: 1024 }, () => ({ gear_params: 0 }));
  const upgrade = Array.from({ length: 1024 }, () => ({ intelligence: 0 }));
  return { tables: { item: { count: 1024, records }, equipment: { count: 1024, records: equipment }, upgrade: { count: 1024, records: upgrade } } };
}

for (const platform of ['pc', 'switch']) {
  test(`${platform}: extra orders preserve adjacent packed bits, currency, flags, gender and trailer`, () => {
    const save = fixture(platform), editor = new OrdersEditor(save);
    const changes = { enemyLevel: 10, noExp: 1, noSkillExp: 1, noTownEvents: 1, showEnemyLevel: 1, showEnemyHp: 1, appearance: 9999 };
    save.data[0x2071e] = 0xdf; save.data[0x2071f] = 0x87;
    const before = save.data.slice();
    editor.apply(changes);
    assert.deepEqual(Object.fromEntries(Object.keys(changes).map(key => [key, editor.values()[key]])), changes);
    assert.equal(save.data[0x2071e], 0xff); assert.equal(save.data[0x2071f], 0xff);
    const addresses = new Set([0x2071e, 0x2071f, 0x2072c, 0x20740, 0x20741, 0x20742, 0x20743]);
    for (let offset = 0; offset < before.length; offset++) if (!addresses.has(offset)) assert.equal(save.data[offset], before[offset], offset.toString(16));
    assert.equal(save.undoStack.length, 1);
    assert.equal(new SaveDocument(save.build()).crcValid, true);
    const after = save.data.slice(); save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.deepEqual(save.data, after);
  });

  for (const preset of ['staff-balanced', 'staff-damage']) test(`${platform}: ${preset} gives six correctly upgraded items without touching worn gear or occupied slots`, () => {
    const save = fixture(platform), catalog = new ItemCatalog(references());
    const before = save.data.slice();
    const preview = gearPreset(preset, catalog);
    assert.equal(preview.exactFinalStats, false); assert.match(preview.source, /80987735/);
    assert.deepEqual(save.data, before);
    giveGearPreset(save, catalog, preset, true);
    const added = save.bagItems().filter(item => item.id && before[item.offset] === 0 && before[item.offset + 1] === 0);
    assert.equal(added.length, 6);
    assert.deepEqual(added.map(item => item.id), [501, 595, 749, 706, 729, 665]);
    const ranges = added.map(item => [item.offset, item.offset + ITEM_RECORD_SIZE]);
    for (let offset = 0; offset < before.length; offset++) if (!ranges.some(([start, end]) => offset >= start && offset < end)) assert.equal(save.data[offset], before[offset], offset.toString(16));
    for (const [i, item] of added.entries()) {
      assert.equal(item.quantity, 1); assert.equal(item.level, 10); assert.ok(item.slot < 60);
      assert.equal(save.data[item.offset + 2], 1);
      const details = itemDetails(save, 'bag', item.slot);
      assert.equal(details.totalLevel, 150); assert.equal(details.rarityBonus, 200);
      assert.deepEqual(Array.from({ length: 3 }, (_, n) => details[`craft${n}`]), preview.items[i].craft.map(entry => entry.id));
      assert.deepEqual(Array.from({ length: 9 }, (_, n) => details[`upgrade${n}`]), preview.items[i].upgrades.map(entry => entry.id));
    }
    assert.equal(save.undoStack.length, 1); assert.equal(new SaveDocument(save.build()).crcValid, true);
    const after = save.data.slice(); save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.deepEqual(save.data, after);
  });

  test(`${platform}: max soil gives positive raw maxima only, preserving unused patches and crops`, () => {
    const save = fixture(platform), editor = new SoilEditor(save);
    for (const farm of SOIL_FARMS) {
      const before = save.data.slice();
      editor.apply(farm.id, farm.patches[0], SOIL_MAXIMUM, true);
      for (const patch of farm.patches) assert.deepEqual(editor.values(farm.id, patch).values, SOIL_MAXIMUM);
      const masks = new Map();
      for (const patch of farm.patches) for (const field of SOIL_FIELDS) for (let i = 0; i < field.width; i++) {
        const offset = editor.values(farm.id, patch).offset + ((field.bit + i) >> 3);
        masks.set(offset, (masks.get(offset) || 0) | (1 << ((field.bit + i) & 7)));
      }
      for (let i = 0; i < before.length; i++) assert.equal((save.data[i] ^ before[i]) & ~(masks.get(i) || 0), 0, i.toString(16));
      assert.equal(new SaveDocument(save.build()).crcValid, true);
      save.undo(); assert.deepEqual(save.data, before);
    }
  });
}

test('extra orders validate the entire request before writing, retaining redo on errors', () => {
  const save = fixture(), editor = new OrdersEditor(save);
  editor.apply({ noExp: 1 }); save.undo();
  const before = save.data.slice();
  for (const changes of [{ noExp: 1, enemyLevel: 127 }, { noExp: 1, noTownEvents: 2 }, { enemyLevel: -1 }, { enemyLevel: 1.5 }, { appearance: 392 }, { appearance: -1 }, { typo: 1 }]) {
    assert.throws(() => editor.apply(changes)); assert.deepEqual(save.data, before); assert.equal(save.redoStack.length, 1);
  }
  assert.ok(ORDER_FIELDS.length > 7);
});

test('gear refuses missing tables, missing consent, full bag and unknown presets atomically', () => {
  const save = fixture(), catalog = new ItemCatalog(references());
  const before = save.data.slice();
  for (const consent of [false, 1, 'true', null]) assert.throws(() => giveGearPreset(save, catalog, 'staff-balanced', consent));
  assert.throws(() => giveGearPreset(save, catalog, 'unknown', true));
  assert.throws(() => giveGearPreset(save, new ItemCatalog(), 'staff-balanced', true));
  const missing = references(); missing.tables.upgrade.records[933] = null;
  assert.throws(() => giveGearPreset(save, new ItemCatalog(missing), 'staff-balanced', true));
  assert.deepEqual(save.data, before); assert.equal(save.undoStack.length, 0);
  for (let slot = 0; slot < 60; slot++) save.view().setUint16(BAG_OFFSET + slot * 28, 501 | (1 << 11), true);
  const full = save.data.slice();
  assert.throws(() => giveGearPreset(save, catalog, 'staff-balanced', true), /Free six/);
  assert.deepEqual(save.data, full); assert.equal(save.undoStack.length, 0);
});

for (const platform of ['pc', 'switch']) for (const preset of ['staff-balanced', 'staff-damage']) {
  test(`${platform}: ${preset} uses scattered empty slots anywhere in the 60-slot bag`, () => {
    const save = fixture(platform), catalog = new ItemCatalog(references());
    const empty = [17, 22, 35, 48, 55, 59];
    for (let slot = 0; slot < 60; slot++) save.view().setUint16(BAG_OFFSET + slot * 28, 501 | (1 << 11), true);
    for (const slot of empty) save.data.fill(0, BAG_OFFSET + slot * 28, BAG_OFFSET + (slot + 1) * 28);
    const before = save.data.slice();
    giveGearPreset(save, catalog, preset, true);
    assert.deepEqual(empty.map(slot => save.bagSlot(slot).id), [501, 595, 749, 706, 729, 665]);
    for (let offset = 0; offset < before.length; offset++) {
      if (!empty.some(slot => offset >= BAG_OFFSET + slot * 28 && offset < BAG_OFFSET + (slot + 1) * 28)) assert.equal(save.data[offset], before[offset]);
    }
    assert.equal(save.undoStack.length, 1); assert.equal(new SaveDocument(save.build()).crcValid, true);
    save.undo(); assert.deepEqual(save.data, before);
  });
}

test('five empty bag slots still refuse an entire set without partial writes or losing redo', () => {
  const save = fixture(), catalog = new ItemCatalog(references());
  save.setPlayer({ money: 1234 }); save.undo();
  for (let slot = 0; slot < 60; slot++) save.view().setUint16(BAG_OFFSET + slot * 28, 501 | (1 << 11), true);
  for (const slot of [18, 34, 47, 58, 59]) save.data.fill(0, BAG_OFFSET + slot * 28, BAG_OFFSET + (slot + 1) * 28);
  const before = save.data.slice();
  assert.throws(() => giveGearPreset(save, catalog, 'staff-damage', true), /Free six bag slots/);
  assert.deepEqual(save.data, before); assert.equal(save.redoStack.length, 1); assert.equal(save.undoStack.length, 0);
});

test('preset sequences honor staff charges, core sets, boot inheritance and the separate damage tradeoff', () => {
  const balanced = GEAR_PRESETS[0], damage = GEAR_PRESETS[1];
  assert.deepEqual(balanced.items[0].upgrades.slice(-3), [909, 884, 567]);
  assert.deepEqual(balanced.items[4].craft, [725, 719, 723]);
  assert.deepEqual(balanced.items[5].craft, [626, 662, 661]);
  assert.deepEqual(damage.items[5].craft, [626, 662, 674]);
  for (const preset of GEAR_PRESETS) for (const item of preset.items.slice(1)) for (const core of [921, 922, 923, 924]) assert.ok(item.upgrades.includes(core));
  assert.equal(SOIL_MAXIMUM.yieldNegative, 0); assert.equal(SOIL_MAXIMUM.qualityNegative, 0); assert.equal(SOIL_MAXIMUM.sizeNegative, 0);
});

test('native mixed gear/order batches roll back everything on failure and have one undo on success', () => {
  call('open', { bytes: call('demoBytes'), name: 'synthetic.sav' }); call('references', { items: references() });
  const before = call('working');
  const gear = { operation: 'setGearPreset', args: { id: 'staff-damage', acknowledgeRisk: true } };
  assert.throws(() => call('applyOperations', { operations: [gear, { operation: 'setOrders', args: { changes: { enemyLevel: 127 } } }] }));
  assert.deepEqual(call('working'), before); assert.equal(call('state').undo, 0);
  call('applyOperations', { operations: [{ operation: 'setOrders', args: { changes: { enemyLevel: 10 } } }, gear] });
  assert.equal(call('state').undo, 1); assert.equal(call('orders').enemyLevel, 10);
  call('undo'); assert.deepEqual(call('working'), before);
});
