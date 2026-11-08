import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { SaveDocument, PLAYER_FIELDS, BAG_OFFSET, BAG_SLOTS, ITEM_RECORD_SIZE, CRC_END } from '../web/save-core.js';
import { ItemCatalog } from '../web/game-reference.js';
import { LOCAL_GAME_DATA } from '../web/local-game-data.js';

const path = process.argv[2];
if (!path) throw new Error('Usage: node tests/verify_real_save.mjs <PC slot save path>. Reads only; never writes a save.');
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const original = readFileSync(path);
const hash = sha256(original);
const save = new SaveDocument(original);
assert.equal(save.crcValid, true, 'Expected a checksum-valid original');
assert.equal(save.playerProfile, true, 'Expected recognized player attributes');
assert.deepEqual(Buffer.from(save.build()), original, 'Unedited save must round trip byte for byte');
console.log('Original player:', Object.fromEntries(Object.keys(PLAYER_FIELDS).map(name => [name, save.player(name)])));
console.log('Original bag:', save.bagItems().filter(item => item.id).map(({ slot, id, quantity, levels }) => ({ slot: slot + 1, id, quantity, levels })));

const catalog = new ItemCatalog(LOCAL_GAME_DATA);
for (const [gender, code] of [['male', 0], ['female', 1]]) {
  const corrected = save.build({ gender, resetAppearance: true });
  const view = new DataView(corrected.buffer);
  assert.equal(corrected[0x36], code);
  assert.equal(view.getUint32(0x38, true), (save.readNumber(0x38, 'u32') & ~1) >>> 0);
  assert.equal(view.getUint32(0x74, true), (save.readNumber(0x74, 'u32') & ~0xfc0000) >>> 0);
  assert.equal(view.getInt32(0x20740, true), 0);
  assert.equal(new SaveDocument(corrected).crcValid, true);
  for (let offset = 4; offset < corrected.length; offset++) {
    if (offset === 0x36 || offset >= 0x38 && offset < 0x3c || offset >= 0x74 && offset < 0x78 || offset >= 0x20740 && offset < 0x20744) continue;
    assert.equal(corrected[offset], original[offset], `Unexpected export override at 0x${offset.toString(16)}`);
  }
  assert.deepEqual(save.data, new Uint8Array(original));
}
save.setPlayer({ money: 12345, prince_points: 99999, max_hp: 100, hp: 80, max_rp: 120, rp: 100, strength: 10, intelligence: 11, vitality: 12 });
save.setBagItem(3, { id: 753, quantity: 8 }, catalog.bagDefinition(753));
save.setBagItem(59, { id: 559, quantity: 1, level: 2 }, catalog.bagDefinition(559));
const output = save.build();
const decoded = new SaveDocument(output);
assert.equal(decoded.crcValid, true);
assert.equal(decoded.player('money'), 12345);
assert.equal(decoded.player('prince_points'), 99999);
assert.equal(decoded.player('max_hp'), 100);
assert.equal(decoded.player('hp'), 80);
assert.equal(decoded.player('strength'), 10);
assert.equal(decoded.bagSlot(3).quantity, 8);
assert.equal(decoded.bagSlot(59).id, 559);
assert.equal(decoded.bagSlot(59).level, 2);
const editedSlots = [3, 59].map(slot => BAG_OFFSET + slot * ITEM_RECORD_SIZE);
for (let offset = 4; offset < output.length; offset++) {
  if (offset >= 0x4c && offset < 0x50 || offset >= 0x54 && offset < 0x6c || offset >= 0x20710 && offset < 0x20714 || editedSlots.some(start => offset >= start && offset < start + ITEM_RECORD_SIZE)) continue;
  assert.equal(output[offset], original[offset], `Unexpected write at 0x${offset.toString(16)}`);
}
for (const name of ['strength', 'intelligence', 'vitality']) assert.equal(output[PLAYER_FIELDS[name].offset + 3], original[PLAYER_FIELDS[name].offset + 3]);
assert.deepEqual(output.subarray(BAG_OFFSET + BAG_SLOTS * ITEM_RECORD_SIZE, 0x20710), new Uint8Array(original.subarray(0x6268, 0x20710)));
assert.deepEqual(output.subarray(0x20714), new Uint8Array(original.subarray(0x20714)));
assert.deepEqual(output.subarray(CRC_END), new Uint8Array(original.subarray(CRC_END)));
assert.deepEqual(save.original, new Uint8Array(original));
for (let edit = 0; edit < 3; edit++) save.undo();
assert.deepEqual(Buffer.from(save.build()), original);
assert.equal(sha256(readFileSync(path)), hash, 'Original file changed during verification');
console.log(`PASS: byte-exact round trip, gender/appearance exports, order points, player/bag edits, undo and CRC; original unchanged. SHA-256 ${hash}`);
