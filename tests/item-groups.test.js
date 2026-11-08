import test from 'node:test';
import assert from 'node:assert/strict';
import { ItemCatalog } from '../web/game-reference.js';

function catalogFixture() {
  return new ItemCatalog({ tables: { item: { count: 7, records: [
    { category: 0, max_stack: 0 },
    { category: 0, max_stack: 9 },
    { category: 46, max_stack: 9 },
    { category: 15, max_stack: 0 },
    { category: 27, max_stack: 0 },
    { category: 55, max_stack: 0 },
    { category: 52, max_stack: 9 },
  ] } } });
}

test('bag browsing groups items by definition category and excludes placeholder records', () => {
  const catalog = catalogFixture();
  const items = catalog.browse({ editableOnly: true });
  assert.equal(items.length, 5);
  assert.equal(items.some(item => item.id === 0 || item.id === 5), false);
  assert.equal(items.find(item => item.id === 3).group, 'weapons');
  assert.equal(items.find(item => item.id === 4).group, 'tools');
  assert.equal(items.find(item => item.id === 2).group, 'seeds');
  assert.equal(items.find(item => item.id === 6).group, 'fish');
  assert.deepEqual(catalog.browse({ group: 'weapons', editableOnly: true }).map(item => item.id), [3]);
  assert.equal(catalog.groups({ editableOnly: true }).find(group => group.id === 'weapons').count, 1);
});

test('group browsing works without a search and search narrows the selected category', () => {
  const catalog = catalogFixture();
  assert.equal(catalog.browse({ group: 'produce', editableOnly: true })[0].name, 'Cabbage');
  assert.deepEqual(catalog.browse({ query: 'cabbage', group: 'produce', editableOnly: true }).map(item => item.id), [1]);
  assert.equal(catalog.browse({ query: 'cabbage', group: 'weapons', editableOnly: true }).length, 0);
  assert.throws(() => catalog.browse({ group: 'invented' }));
});

test('name-only catalog never guesses categories or advertises editable item definitions', () => {
  const catalog = new ItemCatalog();
  const items = catalog.browse({ query: 'Broadsword' });
  assert.equal(items[0].category, null);
  assert.equal(items[0].group, 'other');
  assert.equal(catalog.browse({ editableOnly: true }).length, 0);
});
