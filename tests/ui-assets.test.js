import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PLAYER_FIELDS } from '../web/save-core.js';

const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');

test('all referenced outline icons have a local CSS glyph definition', () => {
  const css = readFileSync(new URL('../web/assets/icons.css', import.meta.url), 'utf8');
  const icons = new Set([...`${html}\n${app}`.matchAll(/\bti-[a-z0-9-]+/g)].map(match => match[0]));
  for (const icon of icons) {
    assert.ok(!icon.endsWith('-filled'), 'Only outline icons are supported');
    assert.ok(css.includes(`.${icon}:before`), `Missing icon glyph: ${icon}`);
  }
});

test('static UI bindings resolve to unique HTML IDs or generated player fields', () => {
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'Duplicate HTML IDs');
  const known = new Set([...ids, ...Object.keys(PLAYER_FIELDS).map(name => `player-${name}`)]);
  for (const [, id] of app.matchAll(/\$\('([^']+)'\)/g)) assert.ok(known.has(id), `Missing UI element: ${id}`);
});

test('expert-only flags, references and raw editing are collapsed off the main interface', () => {
  const start = html.indexOf('<details id="expert-tools"');
  assert.ok(start >= 0, 'Expert tools must have a collapsed details container');
  const opening = html.slice(start, html.indexOf('>', start) + 1);
  assert.ok(!/\bopen(?:\s|=|>)/.test(opening), 'Expert tools must start closed');
  const end = html.indexOf('</details>', start);
  for (const id of ['progress', 'flags', 'items', 'advanced']) {
    const position = html.indexOf(`<section id="${id}"`);
    assert.ok(position > start && position < end, `${id} must be inside expert tools`);
  }
  assert.ok(html.includes('id="bag-group"'), 'Item editing needs a group selector');
  assert.ok(html.includes('id="correct-gender"'), 'Export needs opt-in gender correction');
  assert.ok(html.includes('<div id="player-inputs"></div>'), 'Player groups must stack instead of nesting the groups inside a form grid');
});
