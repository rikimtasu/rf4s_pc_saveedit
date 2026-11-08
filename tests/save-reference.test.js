import test from 'node:test';
import assert from 'node:assert/strict';
import { parseRecipes, SaveReferences } from '../web/save-reference.js';
import { RECIPE_BIT_BASE } from '../web/extended-core.js';

function recipeTable() {
  const bytes = new Uint8Array(28 + 3 * 20 + 16);
  bytes.set(new TextEncoder().encode('NLCL'));
  const view = new DataView(bytes.buffer);
  view.setUint32(16, 1, true); view.setUint32(20, 88, true); view.setUint32(24, 3, true);
  for (const offset of [48, 68]) { view.setUint16(offset, 289, true); view.setUint16(offset + 14, 4, true); view.setUint32(offset + 16, 246, true); }
  return bytes;
}

test('recipe references use global learned bits and preserve linked variants', () => {
  const bytes = recipeTable(); const old = bytes.slice();
  const table = parseRecipes(bytes, 'rf3RecipeCookHandmade.bin');
  assert.equal(table.records.length, 2);
  const refs = new SaveReferences({ recipes: [table] });
  assert.equal(refs.recipes().length, 2);
  assert.equal(refs.recipes()[0].bitOffset, RECIPE_BIT_BASE + 246);
  assert.deepEqual(bytes, old);
  assert.throws(() => refs.add({ kind: 'rf3RecipeDrug', records: [{ ...table.records[0], result: 127 }] }), /overlap/);
  assert.equal(refs.recipes().length, 2);
});

test('recipe import rejects unknown files, corrupt counts and out-of-save flags', () => {
  assert.throws(() => parseRecipes(recipeTable(), 'rf4_s01.sav'));
  const bytes = recipeTable(); new DataView(bytes.buffer).setUint32(24, 1000, true);
  assert.throws(() => parseRecipes(bytes, 'rf3RecipeDrug.bin'));
  assert.throws(() => new SaveReferences({ recipes: [{ kind: 'rf3RecipeDrug', records: [{ index: 1, result: 1, level: 4, bitOffset: 7000 }] }] }));
});
