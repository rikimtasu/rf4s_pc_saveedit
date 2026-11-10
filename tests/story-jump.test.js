import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, SaveDocument, STORY_REGISTER, FLAGS_OFFSET, writeFlag } from '../web/save-core.js';
import { ProgressCatalog } from '../web/progress-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';
import { previewStoryJump, applyStoryJump, explainStoryJump } from '../web/story-jump.js';
import { nativeInvoke as call } from '../web/native-core.js';

const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
const flag = name => catalog.byName.get(name);
const codes = plan => plan.warnings.map(warning => warning.code);

test('multi-flag planning evaluates final combined conditions without touching bytes or undo/redo', () => {
  const save = createDemo();
  save.setFlag(STORY_REGISTER, 430);
  save.setFlag(flag('FLG_SUBEV_COM_49_CLEAR'), 1);
  save.setPlayer({ money: 123 }); save.undo();
  const before = save.data.slice(), original = save.original.slice(), undo = structuredClone(save.undoStack), redo = structuredClone(save.redoStack);
  const plan = previewStoryJump(save, catalog, { target: 440, flags: { FLG_SUBEV_COM_49_CLEAR: 0 } });
  assert.equal(plan.beforeConditions[1].eligibility, 'false');
  assert.equal(plan.afterConditions[1].progressPass, true);
  assert.equal(plan.afterConditions[1].completionPass, true);
  assert.equal(plan.afterConditions[1].eligibility, 'unknown');
  assert.equal(plan.fields.length, 2);
  assert.equal(plan.simulatedEvents, false);
  assert.equal(plan.playableCheckpoint, 'unverified');
  assert.match(explainStoryJump(plan), /Participant-enable runtime queries are unknown/);
  assert.match(explainStoryJump(plan, 'zh'), /总体资格.*未知/);
  assert.deepEqual(save.data, before); assert.deepEqual(save.original, original);
  assert.deepEqual(save.undoStack, undo); assert.deepEqual(save.redoStack, redo);
});

for (const platform of ['pc', 'switch']) test(`${platform}: exact preview bytes match atomic apply, export checksum and undo/redo`, () => {
  const pc = createDemo(), save = platform === 'pc' ? pc : new SaveDocument(pc.build({ platform: 'switch', experimental: true }));
  const options = { target: 442, flags: { REG_MAIN_SCENARIO: 442, FLG_SUBEV_COM_49_CLEAR: 1, REG_SUBEV_AFTER: 96, REG_SUBEV_NOW: 0 }, acknowledgeRisk: true };
  const before = save.data.slice(), neighbor = before[FLAGS_OFFSET + 1] & 0xfe;
  const plan = previewStoryJump(save, catalog, options);
  assert.equal(plan.fields.filter(field => field.name === STORY_REGISTER.name).length, 1);
  assert.equal(applyStoryJump(save, catalog, options), true);
  assert.equal(save.undoStack.length, 1);
  const actual = [];
  for (let offset = 0; offset < save.size; offset++) if (before[offset] !== save.data[offset]) actual.push({ offset, before: before[offset], after: save.data[offset], mask: before[offset] ^ save.data[offset] });
  assert.deepEqual(actual, plan.changes);
  assert.equal(save.data[FLAGS_OFFSET + 1] & 0xfe, neighbor);
  assert.deepEqual(save.original, before);
  const output = save.build(); assert.equal(new SaveDocument(output).crcValid, true);
  assert.equal(applyStoryJump(save, catalog, options), false); assert.equal(save.undoStack.length, 1);
  save.undo(); assert.deepEqual(save.data, before);
  save.redo(); assert.deepEqual(save.build(), output);
  assert.equal(codes(plan).includes('platform'), platform === 'switch');
});

test('invalid requests, conflicts and absent acknowledgements fail with no partial edit', () => {
  const save = createDemo(), before = save.data.slice();
  for (const options of [{ target: '' }, { target: 512 }, { target: 440, flags: [] }, { target: 440, flags: null }, { target: 440, flags: { UNKNOWN: 1 } }, { target: 440, flags: { REG_MAIN_SCENARIO: 442 } }, { target: 440, flags: { REG_SUBEV_NOW: 512 } }, { target: 440 }, { target: 440, acknowledgeRisk: 1 }, { target: 7, acknowledgeRisk: true }]) {
    assert.throws(() => applyStoryJump(save, catalog, options));
    assert.deepEqual(save.data, before); assert.equal(save.undoStack.length, 0);
  }
  const plan = previewStoryJump(save, catalog, { target: 7 });
  assert.equal(plan.direction, 'rewind'); assert.ok(codes(plan).includes('rewind'));
  applyStoryJump(save, catalog, { target: 7, acknowledgeRisk: true, allowRewind: true });
  assert.equal(save.flag(STORY_REGISTER), 7);
});

test('witness mismatch checks never invent completion, restoration or system edits', () => {
  const save = createDemo();
  save.setFlag(flag('FLG_SYELZA_ERACE'), 1); save.setFlag(flag('FLG_SYELZA_SUBEV_STOP'), 1);
  const plan = previewStoryJump(save, catalog, { target: 511 });
  assert.ok(codes(plan).includes('witness-mismatch'));
  assert.equal(plan.witnessChecks.find(check => check.name === 'FLG_SYELZA_ERACE').matches, false);
  assert.deepEqual(plan.fields.map(field => field.name), ['REG_MAIN_SCENARIO']);
  assert.match(explainStoryJump(plan), /250 tourists\/3000 prince points/);
  applyStoryJump(save, catalog, { target: 511, acknowledgeRisk: true });
  assert.equal(save.flag(flag('FLG_SYELZA_ERACE')), 1);
  assert.ok(codes(previewStoryJump(save, catalog, { target: 441 })).includes('unannotated-stage'));
});

test('in-flight events and completion contradictions are disclosed, not silently cleaned', () => {
  const save = createDemo();
  save.setFlag(flag('REG_SUBEV_NOW'), 96); save.setFlag(flag('REG_SUBEV_RSV'), 56);
  const plan = previewStoryJump(save, catalog, { target: 442, flags: { FLG_SUBEV_COM_49_CLEAR: 1 } });
  assert.ok(codes(plan).includes('event-in-flight'));
  assert.ok(codes(plan).includes('active-completed-96'));
  const clear = previewStoryJump(save, catalog, { target: 442, flags: { REG_SUBEV_NOW: 0, REG_SUBEV_AFTER: 96 } });
  assert.ok(codes(clear).includes('event-id-edit')); assert.ok(codes(clear).includes('after-id-edit'));
  assert.equal(clear.afterConditions[1].completionPass, true, 'AFTER alone does not complete Memories');
  assert.equal(save.flag(flag('REG_SUBEV_NOW')), 96);
});

test('missing or mismatched imported evidence is unknown, never a successful check', () => {
  const save = createDemo(), mainOnly = new ProgressCatalog([STORY_REGISTER]);
  const plan = previewStoryJump(save, mainOnly, { target: 442 });
  assert.ok(codes(plan).includes('unknown-event-layout'));
  assert.equal(plan.afterConditions[1].completionPass, null);
  assert.equal(plan.witnessChecks[0].matches, null);
  const shifted = new ProgressCatalog([STORY_REGISTER, { ...flag('FLG_SUBEV_COM_49_CLEAR'), bitOffset: 3000 }]);
  assert.equal(previewStoryJump(save, shifted, { target: 440 }).afterConditions[1].completionPass, null);
});

test('all 512 targets preserve the neighboring register and match planned packed bytes', () => {
  const save = createDemo(), before = save.data.slice();
  for (let target = 0; target <= 511; target++) {
    const plan = previewStoryJump(save, catalog, { target });
    const expected = before.slice(); writeFlag(expected, STORY_REGISTER, target);
    const projected = before.slice(); for (const change of plan.changes) projected[change.offset] = change.after;
    assert.deepEqual(projected, expected);
    assert.equal(projected[FLAGS_OFFSET + 1] & 0xfe, before[FLAGS_OFFSET + 1] & 0xfe);
  }
  assert.deepEqual(save.data, before); assert.equal(save.undoStack.length, 0);
});

test('native planner and pending-edit batch share validation and rollback', () => {
  call('open', { bytes: call('demoBytes'), name: 'synthetic.sav' });
  const before = call('working');
  const options = { target: 440, acknowledgeRisk: true, flags: { FLG_SUBEV_COM_49_CLEAR: 0 } };
  assert.match(call('storyJumpPreview', { ...options, language: 'zh' }).explanation, /离线剧情跳转/);
  assert.deepEqual(call('working'), before);
  assert.throws(() => call('applyOperations', { operations: [{ operation: 'setStoryJump', args: options }, { operation: 'setCalendar', args: { changes: { day: 99, season: 0, year: 1 } } }] }));
  assert.deepEqual(call('working'), before); assert.equal(call('state').undo, 0);
  call('applyOperations', { operations: [{ operation: 'setStoryJump', args: options }, { operation: 'setPlayer', args: { changes: { money: 123 } } }] });
  assert.equal(call('state').undo, 1); assert.equal(call('player').money, 123);
  call('undo'); assert.deepEqual(call('working'), before);
});

test('native story profiles use the same risk/rewind guard rather than bypassing the planner', () => {
  call('open', { bytes: call('demoBytes'), name: 'synthetic.sav' });
  const before = call('working');
  const text = JSON.stringify({ format: 'rf4s-progress-v1', flags: { REG_MAIN_SCENARIO: 7, REG_SUBEV_RSV: 56 } });
  assert.throws(() => call('applyProfile', { text }));
  assert.throws(() => call('applyProfile', { text, acknowledgeRisk: true }));
  assert.deepEqual(call('working'), before); assert.equal(call('state').undo, 0);
  call('applyProfile', { text, acknowledgeRisk: true, allowRewind: true });
  assert.equal(call('state').undo, 1);
  call('undo'); assert.deepEqual(call('working'), before);
});
