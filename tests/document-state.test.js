import test from 'node:test';
import assert from 'node:assert/strict';
import { SaveDocument, createDemo, SYSTEM_SAVE_SIZE, crc32 } from '../web/save-core.js';

function fixture(platform) {
  if (platform !== 'system') return createDemo().build({ platform, experimental: true });
  const bytes = new Uint8Array(SYSTEM_SAVE_SIZE);
  bytes.set(new TextEncoder().encode('RF4D'));
  new DataView(bytes.buffer).setUint32(4, crc32(bytes.subarray(8)), true);
  return bytes;
}

for (const platform of ['pc', 'switch', 'system']) {
  test(`${platform}: export state follows the last exported payload through undo, redo and reset`, () => {
    const save = new SaveDocument(fixture(platform));
    assert.equal(save.exportState, 'original');
    assert.equal(save.undo(), false);
    assert.equal(save.exportState, 'original');
    save.setNumber(0x20, 'u8', 1);
    assert.equal(save.exportState, 'unexported');
    save.build();
    assert.equal(save.exportState, 'unexported', 'Building an output is not exporting it');
    const working = save.data.slice();
    const history = structuredClone(save.undoStack);
    assert.equal(save.markExported(), 'exported');
    assert.deepEqual(save.data, working);
    assert.deepEqual(save.undoStack, history);
    assert.deepEqual(save.original, fixture(platform));
    save.undo();
    assert.equal(save.dirty, false);
    assert.equal(save.exportState, 'unexported', 'Restoring imported bytes must still warn after export');
    save.redo();
    assert.equal(save.exportState, 'exported', 'Undo must not mutate the export checkpoint');
    save.reset();
    assert.equal(save.exportState, 'unexported');
    save.undo();
    assert.equal(save.exportState, 'exported');
    save.redo();
    save.markExported();
    assert.equal(save.exportState, 'exported');
    save.undo();
    assert.equal(save.exportState, 'unexported');
    assert.equal(new SaveDocument(save.original).exportState, 'original');
  });

  test(`${platform}: export state uses net bytes, not history depth or a latched dirty flag`, () => {
    const save = new SaveDocument(fixture(platform));
    save.markExported();
    save.setNumber(0x20, 'u8', 1);
    save.markExported();
    save.setNumber(0x20, 'u8', 2);
    assert.equal(save.exportState, 'unexported');
    save.setNumber(0x20, 'u8', 1);
    assert.equal(save.exportState, 'exported');
    save.undo();
    save.setNumber(0x20, 'u8', 3);
    assert.equal(save.redoStack.length, 0);
    assert.equal(save.exportState, 'unexported');
    assert.throws(() => save.setNumber(0x20, 'u8', 256));
    assert.equal(save.exportState, 'unexported');
  });
}

test('pre-export undo returns to original; export-only overrides do not change payload state', () => {
  const save = createDemo();
  save.setPlayer({ money: 1234 });
  save.undo();
  assert.equal(save.exportState, 'original');
  const before = save.data.slice();
  const redo = structuredClone(save.redoStack);
  save.build({ gender: 'female', resetAppearance: true, platform: 'switch', experimental: true });
  assert.equal(save.exportState, 'original');
  save.markExported();
  assert.equal(save.exportState, 'exported');
  assert.deepEqual(save.data, before);
  assert.deepEqual(save.redoStack, redo);
  save.redo();
  assert.equal(save.exportState, 'unexported');
});
