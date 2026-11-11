import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { SaveDocument, createDemo, FLAGS_OFFSET } from '../web/save-core.js';
import { OrdersEditor, ORDER_FIELDS, ORDER_GROUPS, MORNING_CALLERS } from '../web/orders-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';
import { nativeInvoke as call } from '../web/native-core.js';

const fixture = platform => new SaveDocument(createDemo().build(platform === 'switch' ? { platform, experimental: true } : {}));
const newFields = ORDER_FIELDS.filter(field => field.group !== 'effects');

for (const platform of ['pc', 'switch']) {
  test(`${platform}: each added order field preserves every other bit and supports clear, undo, redo and CRC`, () => {
    const save = fixture(platform), editor = new OrdersEditor(save);
    for (const field of newFields) {
      // Nonzero neighbors catch accidental whole-byte writes. Max isn't enough
      // to catch reversed MSB-first GameFlags; cover 1 and an asymmetric pattern.
      save.data.fill(0xa5, FLAGS_OFFSET, FLAGS_OFFSET + 832);
      save.data.fill(0xa5, 0x20718, 0x20744);
      const values = field.key === 'morningCaller' ? MORNING_CALLERS.map(entry => entry.id) : [...new Set([0, 1, field.max, field.max > 3 ? 5 : 2].filter(n => n <= field.max))];
      for (const value of values) {
        const before = save.data.slice();
        const masks = new Map();
        const width = field.flag?.width ?? field.width ?? (field.type === 'i32' ? 32 : 1);
        for (let bit = 0; bit < width; bit++) {
          const absolute = field.flag ? field.flag.bitOffset + bit : field.offset * 8 + (field.bit || 0) + bit;
          const offset = (field.flag ? FLAGS_OFFSET : 0) + Math.floor(absolute / 8);
          masks.set(offset, (masks.get(offset) || 0) | (1 << (absolute % 8)));
        }
        editor.apply({ [field.key]: value });
        assert.equal(editor.values()[field.key], value, field.key);
        for (let offset = 0; offset < before.length; offset++) assert.equal((save.data[offset] ^ before[offset]) & ~(masks.get(offset) || 0), 0, `${field.key}: ${offset.toString(16)}`);
        if (field.flag) {
          for (let bit = 0; bit < width; bit++) {
            const absolute = field.flag.bitOffset + bit;
            assert.equal((save.data[FLAGS_OFFSET + Math.floor(absolute / 8)] >> (absolute % 8)) & 1, (value >> (width - bit - 1)) & 1, field.key);
          }
        }
        assert.equal(new SaveDocument(save.build()).crcValid, true);
        if (save.undoStack.length) {
          const after = save.data.slice();
          save.undo(); assert.deepEqual(save.data, before); save.redo(); assert.deepEqual(save.data, after); save.undo();
        }
      }
    }
  });
}

test('expanded orders use known symbols at their exact full widths, never the CT partial register widths', () => {
  const symbols = new Map(SAVE_METADATA.symbols.map(field => [field.name, field]));
  const keys = ORDER_FIELDS.map(field => field.key);
  assert.equal(new Set(keys).size, keys.length);
  assert.equal(newFields.filter(field => field.group === 'licenses').length, 7);
  assert.equal(newFields.filter(field => field.group === 'shops').length, 12);
  for (const field of newFields) {
    assert.ok(ORDER_GROUPS.some(group => group.id === field.group));
    if (field.flag) assert.deepEqual(field.flag, { name: field.flag.name, bitOffset: symbols.get(field.flag.name).bitOffset, width: symbols.get(field.flag.name).width });
  }
  assert.equal(ORDER_FIELDS.find(field => field.key === 'storageExpansion').flag.width, 3);
  assert.equal(ORDER_FIELDS.find(field => field.key === 'bagExpansion').flag.width, 2);
  assert.equal(ORDER_FIELDS.find(field => field.key === 'bgm').flag.width, 4);
});

test('raw rank preserves the upper three bits and does not change currency or order-license bits', () => {
  const save = fixture(), editor = new OrdersEditor(save);
  save.data[0x20718] = 0xe0;
  editor.apply({ princeRank: 17 });
  assert.equal(save.data[0x20718], 0xf1);
  assert.equal(editor.values().princeRank, 17);
  assert.equal(save.player('money'), 200);
  assert.equal(editor.values().forgeLicense, 0);
});

test('invalid final expansion/licensing values roll back a mixed batch and preserve redo', () => {
  const save = fixture(), editor = new OrdersEditor(save);
  editor.apply({ forgeLicense: 1 }); save.undo();
  const before = save.data.slice();
  for (const changes of [{ nationalizeBaths: 1, bagExpansion: 4 }, { forgeLicense: 1, fridgeExpansion: 8 }, { businessLicense: 2 }, { princeRank: 32 }, { bgm: 16 }, { fieldExpansion: -1 }]) {
    assert.throws(() => editor.apply(changes)); assert.deepEqual(save.data, before); assert.equal(save.redoStack.length, 1);
  }
  call('open', { bytes: call('demoBytes'), name: 'synthetic.sav' });
  const original = call('working');
  assert.throws(() => call('applyOperations', { operations: [
    { operation: 'setOrders', args: { changes: { airshipLicense: 1, princeRank: 17 } } },
    { operation: 'setOrders', args: { changes: { bagExpansion: 4 } } },
  ] }));
  assert.deepEqual(call('working'), original); assert.equal(call('state').undo, 0);
  call('setOrders', { changes: { airshipLicense: 1, nationalizeBaths: 1, bagExpansion: 1, everyoneSwimsuits: 1 } });
  assert.equal(call('state').undo, 1); call('undo'); assert.deepEqual(call('working'), original);
});

test('optional local CT cross-check confirms packed-license/shop/rank offsets without executing XML scripts', t => {
  const path = new URL('../ct/Rune Factory 4 Special Steam v13_happy.CT', import.meta.url);
  if (!existsSync(path)) { t.skip('Personal CT is not included in source distributions.'); return; }
  const text = readFileSync(path, 'utf8');
  const expected = [
    ['Forge License', 'forgeLicense', 0, 1, 0],
    ['Chemistry License', 'chemistryLicense', 1, 1, 0],
    ['Buisness License', 'businessLicense', 3, 1, 2],
    ['Airship License', 'airshipLicense', 0, 1, 0x1c],
    ['Nationalize Baths', 'nationalizeBaths', 6, 1, 2],
    ['Prince(ss) rank', 'princeRank', 0, 5, -4],
    ['Expanded Cooking Tools', 'expandedCookingTools', 7, 1, 2],
  ];
  for (const [label, key, bit, width, relative] of expected) {
    const start = text.indexOf(`<Description>"${label}"</Description>`);
    assert.ok(start >= 0, label);
    const entry = text.slice(start, text.indexOf('</CheatEntry>', start));
    assert.ok(entry.includes(`<BitStart>${bit}</BitStart>`)); assert.ok(entry.includes(`<BitLength>${width}</BitLength>`));
    const address = relative === 0 ? 'ExpGainPtr' : `ExpGainPtr${relative < 0 ? '-' : '+'}${Math.abs(relative).toString(16).toUpperCase()}`;
    assert.ok(entry.includes(`<Address>${address}</Address>`), label);
    const field = ORDER_FIELDS.find(field => field.key === key);
    assert.equal(field.offset, 0x2071c + relative); assert.equal(field.bit, bit); assert.equal(field.width, width);
  }
});
