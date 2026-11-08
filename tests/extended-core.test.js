import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, INVENTORIES, ITEM_RECORD_SIZE, CRC_END } from '../web/save-core.js';
import { ExtendedSave, SKILLS, STAT_FIELDS, friendshipPoints, friendshipLevel, monsterFriendshipPoints, monsterFriendshipLevel, MONSTER_OFFSET, TROPHIES, RECIPE_BIT_BASE } from '../web/extended-core.js';

function fixture() {
  const seed = createDemo();
  seed.transact('Fixture', bytes => {
    const view = seed.view(bytes);
    bytes.set(new TextEncoder().encode('Shell'), MONSTER_OFFSET);
    view.setUint32(MONSTER_OFFSET + 32, 0x7a531005, true);
    bytes[MONSTER_OFFSET + 20] = 97;
    for (const base of [0xb8 + 100, 0xb44]) {
      for (const spec of Object.values(STAT_FIELDS)) {
        const offset = base + spec.offset;
        if (spec.type === 'u16') view.setUint16(offset, 10, true);
        else view.setUint32(offset, spec.bits ? 0xa500000a : 10, true);
      }
    }
  });
  const save = new SaveDocument(seed.build());
  return { save, editor: new ExtendedSave(save) };
}

test('skills respect per-skill caps and preserve the unused halfword and other slots', () => {
  const { save, editor } = fixture();
  for (const id of [0, 17, 26, 37]) {
    const old = save.data.slice();
    editor.setSkill(id, { level: SKILLS[id].max, xp: 123 });
    assert.equal(editor.skill(id).level, SKILLS[id].max);
    const offset = editor.skill(id).offset;
    for (let i = 4; i < old.length; i++) if (![offset, offset + 1, offset + 4, offset + 5, offset + 6, offset + 7].includes(i)) assert.equal(save.data[i], old[i]);
    assert.throws(() => editor.setSkill(id, { level: SKILLS[id].max + 1 }));
    save.undo();
    assert.deepEqual(save.data, old);
  }
  for (const value of [-1, 38, 1.5]) assert.throws(() => editor.skill(value));
  assert.throws(() => editor.setSkill(0, { xp: 0x1000000 }));
});

test('friendship levels follow executable thresholds including high levels', () => {
  for (let level = 0; level <= 10000; level++) assert.equal(friendshipLevel(friendshipPoints(level)), level);
  const { save, editor } = fixture();
  editor.setFriendship(1, 11);
  assert.equal(save.readNumber(0x1db40, 'i32'), 1681);
  assert.equal(editor.friendship(1).level, 11);
  assert.equal(save.readNumber(0x1db44, 'u32'), 0);
  save.undo();
  save.setNumber(0x1df38, 'u16', 3);
  editor.setFriendship(24, 10);
  assert.equal(save.readNumber(0x1df38, 'u16'), 43);
  assert.equal(editor.friendship(24).level, 10);
  assert.throws(() => editor.setFriendship(1, 10001));
});

test('existing monster friendship does not change name, species, barn, flags or other records', () => {
  for (let level = 0; level <= 1000; level++) assert.equal(monsterFriendshipLevel(monsterFriendshipPoints(level)), level);
  const { save, editor } = fixture();
  const old = save.data.slice();
  editor.setMonsterFriendship(0, 30);
  assert.equal(editor.monster(0).friendship, 30);
  assert.equal(editor.monster(0).name, 'Shell');
  assert.throws(() => editor.setMonsterFriendship(1, 10), /existing/);
  for (let i = 4; i < old.length; i++) if (i !== MONSTER_OFFSET + 24 && i !== MONSTER_OFFSET + 25) assert.equal(save.data[i], old[i]);
  save.undo();
  assert.deepEqual(save.data, save.original);
});

test('people and monster stat writes preserve upper attribute bytes and unedited fields', () => {
  const { save, editor } = fixture();
  for (const [kind, id, base] of [['person', 1, 0x11c], ['monster', 0, 0xb44]]) {
    const old = save.data.slice();
    editor.setStats(kind, id, { strength: 100, level: 50 });
    assert.equal(editor.stats(kind, id).strength, 100);
    assert.equal(save.data[base + 15], 0xa5);
    for (let i = 4; i < old.length; i++) if (i < base + 12 || i >= base + 15 && i < base + 24 || i >= base + 26) assert.equal(save.data[i], old[i]);
    const changed = save.data.slice();
    assert.throws(() => editor.setStats(kind, id, { max_hp: 1 }));
    assert.deepEqual(save.data, changed);
    save.undo();
    assert.deepEqual(save.data, old);
  }
});

test('recipe and trophy edits touch only the verified flag fields and share undo/CRC', () => {
  const { save, editor } = fixture();
  const recipes = [{ bitOffset: RECIPE_BIT_BASE + 1 }, { bitOffset: RECIPE_BIT_BASE + 35 }];
  editor.setRecipes(recipes, true);
  assert.equal(editor.recipe(recipes[0]), true);
  assert.throws(() => editor.setRecipes([{ bitOffset: 4096 }], true));
  assert.throws(() => editor.setRecipes([recipes[0], recipes[0]], true));
  const trophy = TROPHIES.find(v => v.width === 2);
  editor.setTrophy(trophy.name, 3);
  assert.equal(editor.trophy(trophy.name), 3);
  assert.equal(new SaveDocument(save.build()).crcValid, true);
  save.undo(); save.undo();
  assert.deepEqual(save.data, save.original);
});

test('container editing uses verified bounds, preserves metadata and survives conversion', () => {
  const { save } = fixture();
  const definition = { category: 15, max_stack: 0 };
  for (const [container, spec] of Object.entries(INVENTORIES)) {
    const original = save.data.slice();
    save.setInventoryItem(container, spec.slots - 1, { id: 328, quantity: 1, level: 10 }, definition);
    assert.equal(save.inventorySlot(container, spec.slots - 1).id, 328);
    assert.equal(save.inventoryItems(container).length, spec.slots);
    const output = save.build({ platform: 'switch', experimental: true });
    assert.equal(new SaveDocument(output).inventorySlot(container, spec.slots - 1).level, 10);
    const offset = spec.offset + (spec.slots - 1) * ITEM_RECORD_SIZE;
    for (let i = 4; i < original.length; i++) if (i < offset || i >= offset + ITEM_RECORD_SIZE) assert.equal(save.data[i], original[i]);
    assert.deepEqual(save.data.subarray(CRC_END), original.subarray(CRC_END));
    assert.throws(() => save.inventorySlot(container, spec.slots));
    save.undo(); assert.deepEqual(save.data, original);
  }
  assert.throws(() => save.inventorySlot('__proto__', 0));
});

test('combined monster changes are atomic and have one undo entry', () => {
  const { save, editor } = fixture();
  assert.throws(() => editor.setMonster(0, { stats: { level: 50 }, friendship: 1001 }));
  assert.deepEqual(save.data, save.original);
  editor.setMonster(0, { stats: { level: 50 }, friendship: 11 });
  assert.equal(editor.stats('monster', 0).level, 50);
  assert.equal(editor.monster(0).friendship, 11);
  assert.equal(save.undoStack.length, 1);
  save.undo(); assert.deepEqual(save.data, save.original);
});
