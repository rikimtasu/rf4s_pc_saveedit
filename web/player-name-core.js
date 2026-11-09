// The game restores player names from rf4_sys.sav, not individual slot saves.
import { integer, equalBytes } from './save-core.js';

export const NAME_RECORD_COUNT = 40;
export const NAME_RECORD_BASE = 0x4f0;
export const NAME_RECORD_STRIDE = 0xa4;
export const PLAYER_NAME_SIZE = 19; // Six 3-byte characters plus the terminator.

export class PlayerNameEditor {
  constructor(document) { this.document = document; }
  values(recordInput, bytes = this.document.data) {
    if (this.document.kind !== 'system') throw new Error('Open rf4_sys.sav to edit player names.');
    const id = integer(recordInput, 0, NAME_RECORD_COUNT - 1, 'Name record');
    const base = NAME_RECORD_BASE + id * NAME_RECORD_STRIDE;
    const bank = Math.floor(id / 20), slot = id % 20;
    const offset = base + 0x14;
    const stored = bytes.subarray(offset, offset + PLAYER_NAME_SIZE);
    const end = stored.indexOf(0);
    const raw = stored.subarray(0, end < 0 ? stored.length : end);
    const name = new TextDecoder().decode(raw);
    return { id, bank, slot, offset, name, usesDefault: end === 0,
      valid: end >= 0 && equalBytes(new TextEncoder().encode(name), raw),
      present: Boolean(this.document.readNumber(8 + bank * 4, 'u32', bytes) >>> slot & 1),
      gender: this.document.readNumber(base + 0x10, 'u32', bytes) & 1 ? 'female' : 'male' };
  }
  apply(record, name) {
    const person = this.values(record);
    if (!person.present) throw new Error('Select an existing save-slot name record; this does not create a save.');
    if (typeof name !== 'string') throw new Error('Player name must be text.');
    const characters = Array.from(name);
    if (characters.length > 6 || characters.some(char => {
      const code = char.codePointAt(0);
      return code < 32 || code === 127 || code >= 0xd800 && code <= 0xdfff;
    })) throw new Error('Player name allows up to 6 characters, without control characters.');
    const encoded = new TextEncoder().encode(name);
    if (encoded.length >= PLAYER_NAME_SIZE) throw new Error('Player name must fit in 18 UTF-8 bytes.');
    return this.document.transact(`Player name · bank ${person.bank + 1}, slot ${person.slot}`, bytes => {
      bytes.fill(0, person.offset, person.offset + PLAYER_NAME_SIZE);
      bytes.set(encoded, person.offset);
    });
  }
}
