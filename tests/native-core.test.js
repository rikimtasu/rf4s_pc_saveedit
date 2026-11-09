import test from 'node:test';
import assert from 'node:assert/strict';
import { nativeInvoke as call } from '../web/native-core.js';
import { SaveDocument } from '../web/save-core.js';

const fixture = () => call('open', { bytes: call('demoBytes'), name: 'synthetic.sav' });
const items = () => {
  const records = Array.from({ length: 1024 }, () => ({ category: 51, max_stack: 9 }));
  records[328] = { category: 15, max_stack: 1 };
  return { tables: { item: { count: 1024, records }, equipment: { count: 1024, records: Array.from({ length: 1024 }, () => ({ gear_params: 0 })) } } };
};

test('native operation interface round trips originals, changes, undo and converted exports', () => {
  fixture();
  const original = call('original');
  assert.deepEqual(call('build'), original);
  call('setCalendar', { changes: { day: 30, season: 3, year: 4 } });
  call('setPlayer', { changes: { money: 1234 } });
  assert.equal(call('state').undo, 2);
  call('undo'); assert.equal(call('player').money, 200);
  call('redo'); assert.equal(call('player').money, 1234);
  const output = new SaveDocument(call('build', { platform: 'switch', experimental: true }));
  assert.equal(output.crcValid, true); assert.equal(output.get('day'), 30);
  assert.deepEqual(call('original'), original);
  call('reset'); assert.deepEqual(call('working'), original);
});

test('native operations preserve attachments and validate marriage, skills and friendship', () => {
  fixture(); call('references', { items: items() });
  call('setItem', { container: 'bag', slot: 0, changes: { id: 328, quantity: 1 }, details: { craft0: 839, element: 1 } });
  const item = call('item', { container: 'bag', slot: 0 });
  assert.equal(item.element, 1); assert.equal(item.details.craft0, 839); assert.equal(item.level, 3);
  call('setMarriage', { candidate: 17, changes: { spouse: 17, day: 30 } });
  assert.equal(call('marriage', { candidate: 17 }).spouse, 17);
  call('setSkill', { id: 17, changes: { level: 99 } });
  assert.equal(call('skills')[17].level, 99);
  call('setFriendship', { id: 1, level: 10 }); assert.equal(call('friendship')[0].level, 10);
  const before = call('working');
  assert.throws(() => call('setMarriage', { candidate: 17, changes: { spouse: 3 } }));
  assert.throws(() => call('setSkill', { id: 17, changes: { level: 100 } }));
  assert.deepEqual(call('working'), before);
  assert.equal(new SaveDocument(call('build')).crcValid, true);
});

test('native save seam has no browser globals, server or arbitrary-code operation', () => {
  fixture();
  assert.throws(() => call('eval', { text: '1+1' }), /Unknown native/);
  assert.equal(call('monsters').length, 0);
  assert.equal(call('constants').inventories.fridge.slots, 990);
});

test('native dating cleanup previews its targets and applies only on opted-in export', () => {
  fixture();
  call('setNumber', { offset: 0x1db48, type: 'u32', value: 0x400302 });
  call('patchBytes', { offset: 0x1db4c, text: '61' });
  const before = call('working');
  assert.deepEqual(call('datingCleanup', { gender: 'male' }).map(person => person.id), [1, 5, 8, 9, 15, 20]);
  const output = new SaveDocument(call('build', { gender: 'male', resetDating: true }));
  assert.equal(output.crcValid, true);
  assert.equal(output.readNumber(0x1db48, 'u32'), 0x302);
  assert.equal(output.data[0x1db4c], 24);
  assert.deepEqual(call('working'), before);
});

test('native operations expose dating and both nickname fields without altering friendship', () => {
  fixture();
  const before = call('working');
  call('setRelationship', { id: 1, changes: { dating: 1, npcCallsPlayer: 97, playerCallsNpc: 133 } });
  const person = call('relationships')[0];
  assert.deepEqual([person.dating, person.npcCallsPlayer, person.playerCallsNpc], [1, 97, 133]);
  assert.equal(call('friendship')[0].points, 0);
  assert.equal(call('relationships').length, 23);
  call('undo'); assert.deepEqual(call('working'), before);
});
