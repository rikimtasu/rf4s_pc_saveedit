import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = name => readFileSync(path.join(root, name), 'utf8');

test('runtime and maintenance scripts have no machine-specific filesystem literals', () => {
  const files = ['serve.py', 'desktop.py', 'native_ui.py', 'native_save.py', 'start.bat', 'README.md', ...readdirSync(path.join(root, 'web')).filter(name => /\.(js|html)$/.test(name) && !name.startsWith('local-') && name !== 'native-bundle.js').map(name => `web/${name}`), ...readdirSync(path.join(root, 'scripts')).filter(name => name.endsWith('.py')).map(name => `scripts/${name}`)];
  const machinePath = /(?:^|[\s"'])(?:[A-Za-z]:[\\/]|\/(?:Users|home|tmp)\/)/m;
  for (const file of files) assert.equal(machinePath.test(read(file)), false, `Machine-specific path in ${file}`);
  assert.ok(read('start.bat').includes('%~dp0'));
  assert.ok(read('serve.py').includes('Path(__file__).resolve().parent'));
});

test('personal saves, CTs, exports and reference modules are excluded from publication', () => {
  const ignored = read('.gitignore').split(/\r?\n/);
  for (const entry of ['*.sav', '*.changes.json', '/ct/', '/switch_save/', '/exports/', '/dist/', 'web/local-game-data.js', 'web/local-save-reference.js', 'web/local-languages.js']) assert.ok(ignored.includes(entry), entry);
});
