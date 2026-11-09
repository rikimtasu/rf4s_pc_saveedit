import test from 'node:test';
import assert from 'node:assert/strict';
import { nativeInvoke as call } from '../web/native-core.js';
import { createDemo, SaveDocument } from '../web/save-core.js';

test('tourist edits use the audited field and preserve adjacent order points and bytes', () => {
  const save = createDemo(), before = save.data.slice();
  save.setPlayer({ tourists: 99999999 });
  assert.equal(save.readNumber(0x20714, 'i32'), 99999999);
  for (let i = 0; i < before.length; i++) if (i < 0x20714 || i >= 0x20718) assert.equal(save.data[i], before[i]);
  assert.equal(new SaveDocument(save.build()).player('tourists'), 99999999);
  assert.throws(() => save.setPlayer({ tourists: 100000000 }));
  save.undo(); assert.deepEqual(save.data, before);
});

test('automatic draft batches are atomic, undoable and reject invalid or non-edit operations', () => {
  call('open', { bytes: call('demoBytes'), name: 'rf4_s01.sav' });
  const before = call('working');
  const operations = [{ operation: 'setPlayer', args: { changes: { tourists: 2345 } } },
    { operation: 'setFriendship', args: { id: 24, level: 10 } }];
  call('applyOperations', { operations });
  assert.equal(call('player').tourists, 2345);
  assert.equal(call('friendship')[23].level, 10);
  assert.equal(call('state').undo, 1);
  call('undo'); assert.deepEqual(call('working'), before);
  assert.throws(() => call('applyOperations', { operations: [...operations, { operation: 'setPlayer', args: { changes: { money: -1 } } }] }));
  assert.deepEqual(call('working'), before);
  assert.equal(call('state').undo, 0);
  assert.throws(() => call('applyOperations', { operations: [{ operation: 'open', args: { bytes: before } }] }));
  assert.deepEqual(call('working'), before);
});
