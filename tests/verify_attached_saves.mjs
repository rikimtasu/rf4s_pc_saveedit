import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { SaveDocument, FLAGS_OFFSET } from '../web/save-core.js';
import { ProgressCatalog } from '../web/progress-core.js';
import { SAVE_METADATA } from '../web/save-metadata.js';

const directory = process.argv[2];
if (!directory) throw new Error('Usage: node tests/verify_attached_saves.mjs <Switch save directory> [PC slot path] [PC system path]. Read-only.');
const files = [...readdirSync(directory).filter(name => name.endsWith('.sav')).map(name => join(directory, name)), ...process.argv.slice(3)];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const catalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
for (const path of files) {
  const original = readFileSync(path);
  const checksum = hash(original);
  const save = new SaveDocument(original, path);
  assert.equal(save.crcValid, true, `Invalid checksum: ${path}`);
  assert.deepEqual(Buffer.from(save.build()), original);
  if (save.kind === 'system') {
    save.setSystemFlags({ 5: 1 - save.systemFlag(5) });
    const output = save.build();
    assert.equal(new SaveDocument(output).crcValid, true);
    assert.deepEqual(output.subarray(12), new Uint8Array(original.subarray(12)));
    save.undo();
  } else {
    assert.equal(save.playerProfile, true);
    const target = save.platform === 'pc' ? 'switch' : 'pc';
    const converted = save.build({ platform: target, experimental: true });
    const other = new SaveDocument(converted);
    assert.equal(other.crcValid, true);
    assert.deepEqual(other.bagItems(), save.bagItems());
    assert.deepEqual(catalog.snapshot(other), catalog.snapshot(save));
    assert.deepEqual(Buffer.from(other.build({ platform: save.platform, experimental: true })), original);
    save.setPlayer({ lumber: save.player('lumber') === 50000 ? 49999 : save.player('lumber') + 1 });
    save.setFlags(catalog.entries({ REG_MAIN_SCENARIO: 430, REG_SUBEV_RSV: 56, REG_QUEST_AFTER: 200 }));
    const output = save.build();
    assert.equal(new SaveDocument(output).crcValid, true);
    for (let offset = 4; offset < output.length; offset++) {
      if (offset >= 0x3c && offset < 0x40 || offset >= FLAGS_OFFSET && offset < FLAGS_OFFSET + 832) continue;
      assert.equal(output[offset], original[offset], `Unexpected write at ${offset}`);
    }
    save.undo();
    save.undo();
  }
  assert.deepEqual(Buffer.from(save.build()), original);
  assert.equal(hash(readFileSync(path)), checksum, `Source changed: ${path}`);
  console.log(`PASS ${save.kind} / ${save.platform}: ${path}; unchanged SHA-256 ${checksum}`);
}
console.log('Read-only byte-exact round trips, conversion round trips and in-memory edits passed. These are not in-game loading tests.');
