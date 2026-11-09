import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo, FLAGS_OFFSET, STORY_REGISTER } from '../web/save-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';
import { flagHelp, previewFlagEdit, storyConditions } from '../web/flag-help.js';

const field = name => [...SAVE_METADATA.symbols, ...SAVE_METADATA.ctFlags].find(variable => variable.name === name);

test('curated flag help preserves symbols/original descriptions and refuses mismatched semantic annotations', () => {
  const main = field('REG_MAIN_SCENARIO');
  const help = flagHelp(main);
  assert.equal(help.title.zh, '主线剧情进度');
  assert.equal(help.original, main.description);
  assert.ok(help.impact.zh.includes('只向前推进'));
  assert.ok(help.sources.includes('docs/story-flag-investigation.md'));
  const mismatched = flagHelp({ ...main, bitOffset: 9 });
  assert.equal(mismatched.evidence, 'Unknown or mismatched layout');
  assert.equal(mismatched.translation, 'symbol interpretation');
  assert.ok(!mismatched.impact.zh.includes('≥430'));
  assert.equal(main.name, 'REG_MAIN_SCENARIO');
});

test('Memories and Running Sign numeric gates never invent resolved participant eligibility', () => {
  const save = createDemo();
  save.setFlag(STORY_REGISTER, 440);
  const result = storyConditions(save.data);
  assert.ok(result.every(gate => gate.progressPass && gate.completionPass && gate.eligibility === 'unknown'));
  assert.deepEqual(result.find(gate => gate.event === 96).participants, [9, 5, 17, 8, 13, 20]);
  save.setFlag(field('FLG_SUBEV_COM_49_CLEAR'), 1);
  assert.equal(storyConditions(save.data).find(gate => gate.event === 96).eligibility, 'false');
});

test('read-only flag preview follows full-width MSB-first storage and preserves source/history', () => {
  const save = createDemo();
  save.setFlag(STORY_REGISTER, 442); save.setPlayer({ money: 900 }); save.undo();
  const bytes = save.data.slice(), undo = save.undoStack.slice(), redo = save.redoStack.slice();
  const result = previewFlagEdit(save, field('REG_MAIN_SCENARIO'), 430);
  assert.equal(result.rewind, true); assert.equal(result.simulatedEvents, false);
  assert.equal(result.from, 442); assert.equal(result.to, 430);
  assert.ok(result.changes.every(change => change.offset === FLAGS_OFFSET || change.offset === FLAGS_OFFSET + 1));
  const expected = createDemo(); expected.setFlag(STORY_REGISTER, 430);
  for (const change of result.changes) assert.equal(change.after, expected.data[change.offset]);
  assert.deepEqual(save.data, bytes); assert.deepEqual(save.undoStack, undo); assert.deepEqual(save.redoStack, redo);
});

test('completion preview changes only the intended field, not NOW/AFTER or other dependencies', () => {
  const save = createDemo(); save.setFlag(STORY_REGISTER, 440);
  save.setFlag(field('REG_SUBEV_NOW'), 96);
  const result = previewFlagEdit(save, field('FLG_SUBEV_COM_49_CLEAR'), 1);
  assert.equal(result.afterConditions.find(gate => gate.event === 96).eligibility, 'false');
  assert.ok(result.help.impact.zh.includes('不会执行'));
  assert.equal(save.flag(field('REG_SUBEV_NOW')), 96);
  assert.equal(save.flag(field('FLG_SUBEV_COM_49_CLEAR')), 0);
  assert.throws(() => previewFlagEdit(save, field('REG_MAIN_SCENARIO'), 512));
});
