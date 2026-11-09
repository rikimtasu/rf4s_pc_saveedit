import test from 'node:test';
import assert from 'node:assert/strict';
import { parseGameText, languageTable, LanguageCatalog } from '../web/language-core.js';
import { ItemCatalog } from '../web/game-reference.js';

function text(names) {
  const strings = names.map(name => new TextEncoder().encode(name));
  const bytes = new Uint8Array(8 + names.length * 8 + strings.reduce((sum, bytes) => sum + bytes.length + 1, 0));
  bytes.set(new TextEncoder().encode('TEXT')); const view = new DataView(bytes.buffer); view.setUint32(4, names.length, true);
  let offset = 8 + names.length * 8;
  for (const [index, value] of strings.entries()) { view.setUint32(8 + index * 8, value.length, true); view.setUint32(12 + index * 8, offset, true); bytes.set(value, offset); offset += value.length + 1; }
  return bytes;
}

test('game TEXT parser handles UTF-8 languages and index-aligned names', () => {
  const names = ['（无）', '卷心菜', 'キャベツ', '양배추', 'Chou'];
  assert.deepEqual(parseGameText(text(names)), names);
  const table = languageTable('rf3TxtItem_split2_1.chn', text(names));
  const languages = new LanguageCatalog(); languages.add(table); languages.select('zh-Hans');
  const items = new ItemCatalog(null, languages);
  assert.equal(items.name(1), '卷心菜'); assert.equal(items.name(753), 'Turnip Seeds');
  assert.equal(items.browse({ query: '卷心' })[0].id, 1);
  assert.equal(languages.name('people', 1, 'Vishnal'), 'Vishnal');
  assert.throws(() => languageTable('rf3TxtItem_split2_2.eng', text(names)), /not descriptions/);
});

test('language import rejects truncation, UTF-8 damage and strings inside record headers', () => {
  const bytes = text(['Empty', 'Cabbage']);
  assert.throws(() => parseGameText(bytes.slice(0, -1)), /bounds/);
  const pointer = bytes.slice(); new DataView(pointer.buffer).setUint32(12, 4, true); assert.throws(() => parseGameText(pointer), /bounds/);
  const bad = bytes.slice(); bad[24] = 0xff; assert.throws(() => parseGameText(bad));
  assert.throws(() => parseGameText(new Uint8Array(7)));
  const languages = new LanguageCatalog({ languages: { ja: { label: '日本語', items: ['なし'] } } });
  assert.throws(() => languages.merge({ languages: { fr: { items: ['Rien'] }, xx: { items: ['Bad'] } } }));
  assert.equal(languages.languages.has('fr'), false);
  assert.throws(() => languages.select('ko'), /game first/);
});
