import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { SaveDocument, INVENTORIES, ITEM_RECORD_SIZE, equalBytes } from '../web/save-core.js';
import { ExtendedSave, SKILLS, STAT_FIELDS, TROPHIES, RECIPE_BIT_BASE } from '../web/extended-core.js';

const path = process.argv[2];
if (!path) throw new Error('Usage: node tests/verify_extended_save.mjs <PC-or-Switch-slot.sav>. Reads only.');
const original = readFileSync(path);
const save = new SaveDocument(original);
const editor = new ExtendedSave(save);
assert.equal(save.crcValid, true);
assert.deepEqual(Buffer.from(save.build()), original);
const cases = [
  ['Skill level / XP', () => editor.setSkill(0, { level: 77, xp: 0 }), [[0x5964, 0x5966], [0x5968, 0x596c]]],
  ['Friendship', () => editor.setFriendship(1, 12), [[0x1db40, 0x1db44]]],
  ['Guest friendship', () => editor.setFriendship(24, 10), [[0x1df38, 0x1df3a]]],
  ['Person stats', () => editor.setStats('person', 1, { level: 589 }), [[0x134, 0x136]]],
  ['Recipe state', () => editor.setRecipes([{ bitOffset: RECIPE_BIT_BASE + 1 }], !editor.recipe({ bitOffset: RECIPE_BIT_BASE + 1 })), [[0x1e8c4 + ((RECIPE_BIT_BASE + 1) >> 3), 0x1e8c4 + ((RECIPE_BIT_BASE + 1) >> 3) + 1]]],
];
const monster = editor.monsters().find(monster => monster.occupied);
if (monster) cases.push(['Monster stats / friendship', () => editor.setMonster(monster.id, { stats: { level: 315 }, friendship: 12 }), [[0xb44 + monster.id * 100 + 24, 0xb44 + monster.id * 100 + 26], [monster.offset + 24, monster.offset + 26]]]);
for (const [container, spec] of Object.entries(INVENTORIES)) {
  const slot = spec.slots - 1;
  const offset = spec.offset + slot * ITEM_RECORD_SIZE;
  cases.push([spec.label, () => save.setInventoryItem(container, slot, { id: 328, quantity: 1, level: 7 }, { category: 15, max_stack: 0 }), [[offset, offset + ITEM_RECORD_SIZE]]]);
}
for (const [name, edit, ranges] of cases) {
  edit();
  const output = save.build();
  assert.equal(new SaveDocument(output).crcValid, true);
  for (let offset = 4; offset < output.length; offset++) if (!ranges.some(([start, end]) => start <= offset && offset < end)) assert.equal(output[offset], original[offset], `${name}: unexpected byte ${offset.toString(16)}`);
  save.undo();
  assert.deepEqual(Buffer.from(save.build()), original);
  console.log(`PASS: ${name}, CRC, exact byte preservation and undo`);
}
const trophy = TROPHIES[0];
editor.setTrophy(trophy.name, 1 - editor.trophy(trophy.name));
assert.equal(new SaveDocument(save.build()).crcValid, true);
save.undo();
assert.deepEqual(Buffer.from(save.build()), original);
assert.ok(equalBytes(readFileSync(path), original), 'Original file changed during verification');
console.log(`PASS: ${SKILLS.length} named skills, ${TROPHIES.length} trophy/result records, ${Object.keys(STAT_FIELDS).length} stat fields; original unchanged.`);
