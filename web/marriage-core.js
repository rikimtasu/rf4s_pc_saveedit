import { SAVE_METADATA } from './save-metadata.js';
import { integer } from './save-core.js';

export const MARRIAGE_CANDIDATES = [
  [1, 'Vishnal', 'VIZNAR'], [2, 'Clorica', 'CLORICA'], [4, 'Forte', 'FORTE'],
  [5, 'Kiel', 'KEEL'], [7, 'Margaret', 'MARGUERITE'], [8, 'Dylas', 'DIRUS'],
  [9, 'Arthur', 'ARTHUR'], [11, 'Xiao Pai', 'SYAOPAI'], [13, 'Amber', 'KOHAKU'],
  [15, 'Doug', 'DAG'], [17, 'Dolce', 'DOLCE'], [20, 'Leon', 'LEON'],
].map(([id, name, symbol]) => ({ id, name, symbol }));
export const MARRIAGE_FIELDS = [
  { key: 'spouse', name: 'REG_WIFE_ID', label: 'Spouse', min: 0, max: 31 },
  { key: 'season', name: 'REG_MARRIGE_SEASON', label: 'Anniversary season', min: 0, max: 3 },
  { key: 'day', name: 'REG_MARRIGE_DAY', label: 'Anniversary day (0 = unset)', min: 0, max: 30 },
  { key: 'proposal', name: 'FLG_PROPOSE', label: 'Can receive engagement ring', min: 0, max: 1 },
  { key: 'anniversaryTalk', name: 'FLG_MARRIGE_DAY_TALK', label: 'Anniversary conversation recorded', min: 0, max: 1 },
  { key: 'weddingMemory', name: 'FLG_WEDDING_OMOIDE', label: 'Wedding memory flag', min: 0, max: 1 },
];

export class MarriageEditor {
  constructor(document, symbols = SAVE_METADATA.symbols) { this.document = document; this.byName = new Map(symbols.map(field => [field.name, field])); }
  field(name) {
    const expected = SAVE_METADATA.symbols.find(field => field.name === name);
    const field = this.byName.get(name);
    if (!field || field.bitOffset !== expected?.bitOffset || field.width !== expected?.width) throw new Error(`Unrecognized marriage layout: ${name}.`);
    return field;
  }
  values() { return Object.fromEntries(MARRIAGE_FIELDS.map(field => [field.key, this.document.flag(this.field(field.name))])); }
  candidate(id) {
    const person = MARRIAGE_CANDIDATES.find(person => person.id === Number(id));
    if (!person) throw new Error('Choose a marriage candidate.');
    return person;
  }
  eventFields(id) {
    const person = this.candidate(id);
    return { marriageEvent: this.field(`FLG_SUBEV_${person.symbol}_MARRIAGE_CLEAR`), newlywedEvent: this.field(`FLG_SUBEV_${person.symbol}_JUST_MARRIED_CLEAR`) };
  }
  events(id) { return Object.fromEntries(Object.entries(this.eventFields(id)).map(([key, field]) => [key, this.document.flag(field)])); }
  apply(changes, candidateId) {
    const fields = new Map(MARRIAGE_FIELDS.map(field => [field.key, field]));
    const entries = Object.entries(changes).map(([key, value]) => {
      if (key === 'marriageEvent' || key === 'newlywedEvent') return { variable: this.eventFields(candidateId)[key], value: integer(value, 0, 1, key) };
      const spec = fields.get(key);
      if (!spec) throw new Error('Unknown marriage field.');
      const parsed = integer(value, spec.min, spec.max, spec.label);
      if (key === 'spouse' && parsed !== 0 && !MARRIAGE_CANDIDATES.some(person => person.id === parsed)) throw new Error('Choose none or a known marriage candidate.');
      return { variable: this.field(spec.name), value: parsed };
    });
    return this.document.setFlags(entries, 'Marriage flags (events not simulated)');
  }
}
