// Saved relationship flags and address selectors; no romance-event simulation.
import { integer, DATING_CANDIDATES } from './save-core.js';
import { PEOPLE_NAMES } from './extended-core.js';

export const NICKNAME_COUNT = 186;
const DATING_MASK = 0x400000;
const ADDRESS_MASK = 0x7f80;

export class RelationshipEditor {
  constructor(document) { this.document = document; }
  values(idInput, bytes = this.document.data) {
    this.document.requireSlot();
    const id = integer(idInput, 1, 23, 'Relationship person');
    const offset = 0x1db40 + (id - 1) * 44;
    return {
      id, name: PEOPLE_NAMES[id], offset,
      canDate: DATING_CANDIDATES.some(person => person.id === id),
      dating: Number(Boolean(this.document.readNumber(offset + 8, 'u32', bytes) & DATING_MASK)),
      npcCallsPlayer: bytes[offset + 12],
      playerCallsNpc: this.document.readNumber(offset + 20, 'u32', bytes) >>> 7 & 255,
      defaults: {
        male: { npcCallsPlayer: 23 + id, playerCallsNpc: id },
        female: { npcCallsPlayer: 70 + id, playerCallsNpc: 47 + id },
      },
    };
  }
  currentGenderDefaults(id) {
    const person = this.values(id);
    const gender = this.document.gender();
    if (!gender) throw new Error('Saved gender is unrecognized. Cannot choose Lest / Frey nickname defaults.');
    return { id: person.id, gender, defaults: { ...person.defaults[gender] } };
  }
  apply(id, changes, { experimental = false } = {}) {
    const person = this.values(id);
    const parsed = Object.fromEntries(Object.entries(changes).map(([key, value]) => {
      if (!['dating', 'npcCallsPlayer', 'playerCallsNpc'].includes(key)) throw new Error('Unknown relationship field.');
      if (key === 'dating' && !person.canDate && experimental !== true) throw new Error('Dating outside marriage candidates requires experimental consent.');
      return [key, integer(value, 0, key === 'dating' ? 1 : NICKNAME_COUNT - 1, key)];
    }));
    return this.document.transact(`${person.name} relationship (events not simulated)`, bytes => {
      const view = this.document.view(bytes);
      if (parsed.dating !== undefined) {
        const flags = view.getUint32(person.offset + 8, true);
        view.setUint32(person.offset + 8, (parsed.dating ? flags | DATING_MASK : flags & ~DATING_MASK) >>> 0, true);
      }
      if (parsed.npcCallsPlayer !== undefined) bytes[person.offset + 12] = parsed.npcCallsPlayer;
      if (parsed.playerCallsNpc !== undefined) {
        const flags = view.getUint32(person.offset + 20, true);
        view.setUint32(person.offset + 20, (flags & ~ADDRESS_MASK | parsed.playerCallsNpc << 7) >>> 0, true);
      }
    });
  }
}
