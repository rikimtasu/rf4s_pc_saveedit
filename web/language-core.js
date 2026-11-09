import { integer } from './save-core.js';

export const GAME_LANGUAGES = {
  eng: { code: 'en', label: 'English' }, jpn: { code: 'ja', label: '日本語' },
  fra: { code: 'fr', label: 'Français' }, deu: { code: 'de', label: 'Deutsch' },
  kor: { code: 'ko', label: '한국어' }, twn: { code: 'zh-Hant', label: '繁體中文' },
  chn: { code: 'zh-Hans', label: '简体中文' },
};

export function parseGameText(input) {
  const bytes = new Uint8Array(input);
  if (bytes.length < 8 || bytes.length > 16 * 1024 * 1024 || String.fromCharCode(...bytes.subarray(0, 4)) !== 'TEXT') throw new Error('Expected an extracted TEXT language table.');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const count = integer(view.getUint32(4, true), 0, 10000, 'Text count');
  const end = 8 + count * 8;
  if (end > bytes.length) throw new Error('Truncated TEXT records.');
  const decoder = new TextDecoder('utf-8', { fatal: true });
  return Array.from({ length: count }, (_, index) => {
    const size = view.getUint32(8 + index * 8, true);
    const offset = view.getUint32(12 + index * 8, true);
    if (size > 65536 || offset < end || offset + size >= bytes.length || bytes[offset + size] !== 0) throw new Error('Invalid TEXT string bounds.');
    return decoder.decode(bytes.subarray(offset, offset + size));
  });
}

export function languageTable(filename, input) {
  const match = /^rf3Txt(Item|Npc|Skill)_split2_1\.(eng|jpn|fra|deu|kor|twn|chn)$/i.exec(filename);
  if (!match) throw new Error('Choose rf3TxtItem, Npc or Skill_split2_1 language files (not descriptions).');
  const locale = GAME_LANGUAGES[match[2].toLowerCase()];
  return { ...locale, kind: { item: 'items', npc: 'people', skill: 'skills' }[match[1].toLowerCase()], names: parseGameText(input) };
}

export class LanguageCatalog {
  constructor(local = null) { this.languages = new Map(); this.code = 'en'; if (local) this.merge(local); }
  merge(data) {
    const staged = new Map(this.languages);
    for (const [code, entry] of Object.entries(data.languages || {})) {
      if (!Object.values(GAME_LANGUAGES).some(locale => locale.code === code)) throw new Error('Unsupported game language.');
      const next = { ...staged.get(code), label: String(entry.label || code) };
      for (const kind of ['items', 'people', 'skills']) if (entry[kind]) {
        if (!Array.isArray(entry[kind]) || entry[kind].length > 10000 || entry[kind].some(name => typeof name !== 'string' || name.length > 65536)) throw new Error('Invalid language names.');
        next[kind] = entry[kind].slice();
      }
      staged.set(code, next);
    }
    this.languages = staged;
  }
  add(table) { this.merge({ languages: { [table.code]: { label: table.label, [table.kind]: table.names } } }); }
  select(code) { if (code !== 'en' && !this.languages.has(code)) throw new Error('Read this language from your game first.'); this.code = code; }
  name(kind, id, fallback) { return this.languages.get(this.code)?.[kind]?.[id] || fallback; }
  options() { return [{ code: 'en', label: 'English' }, ...[...this.languages].filter(([code]) => code !== 'en').map(([code, entry]) => ({ code, label: entry.label }))]; }
}
