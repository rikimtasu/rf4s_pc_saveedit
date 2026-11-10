// Experimental offline roster creation. No game-definition changes or NPC conversion.
import { integer } from './save-core.js';
import { ExtendedSave, MONSTER_OFFSET, MONSTER_STRIDE, MONSTER_COUNT, STAT_FIELDS, monsterFriendshipPoints } from './extended-core.js';
import { SAVE_METADATA } from './save-metadata.js';

const rooms = SAVE_METADATA.symbols.filter(field => /^REG_MON_HOUSE[0-4]_[LR]_LV$/.test(field.name)).sort((a, b) => a.bitOffset - b.bitOffset);
export class RosterEditor {
  constructor(document) { this.document = document; this.extra = new ExtendedSave(document); }
  housing() {
    this.document.requireSlot();
    const monsters = this.extra.monsters().filter(monster => monster.occupied);
    return rooms.map((field, barn) => {
      const count = this.document.flag(field);
      // Taming routine uses five rooms per barn, four occupants per built room.
      if (count > 5) throw new Error('Unrecognized barn room count (expected 0–5).');
      return Array.from({ length: count }, (_, room) => {
        const map = 77 + barn * 5 + room;
        const occupants = monsters.filter(monster => monster.barn === map).length;
        return { map, barn, room, occupants, free: Math.max(0, 4 - occupants) };
      });
    }).flat();
  }
  add({ species: input, slot: slotInput, room: roomInput, name = '', friendship = 0, sourceKind = 'basic', sourceId = 0, stats = {}, acknowledgeRisk = false } = {}) {
    this.document.requireSlot();
    if (acknowledgeRisk !== true) throw new Error('Acknowledge experimental roster creation first.');
    const species = integer(input, 1, 255, 'NPC / monster species ID');
    if (typeof name !== 'string' || Array.from(name).length > 6 || new TextEncoder().encode(name).length > 18 || /[\u0000-\u001f\u007f]/.test(name)) throw new Error('Roster name must be at most 6 characters / 18 UTF-8 bytes without control characters.');
    const monster = slotInput === undefined || slotInput === null || slotInput === '' ? this.extra.monsters().find(record => !record.occupied) : this.extra.monster(integer(slotInput, 0, MONSTER_COUNT - 1, 'Monster slot'));
    if (!monster || monster.occupied) throw new Error('Choose an empty monster roster slot. Existing monsters are never overwritten.');
    const housing = this.housing();
    const room = roomInput === undefined || roomInput === null || roomInput === '' ? housing.find(room => room.free > 0) : housing.find(room => room.map === integer(roomInput, 77, 126, 'Barn room map'));
    if (!room || room.free < 1) throw new Error('Build a barn room with a free place first (four monsters per room).');
    const points = monsterFriendshipPoints(friendship);
    let source;
    if (sourceKind === 'monster') source = this.extra.statsOffset('monster', sourceId);
    else if (sourceKind === 'person') source = this.extra.statsOffset('person', sourceId);
    else if (sourceKind !== 'basic') throw new Error('Choose basic, person or existing monster stats.');
    // Copy the complete audited stat block, never a live actor/pointer or roster flags.
    const block = source === undefined ? new Uint8Array(100) : this.document.data.slice(source, source + 100);
    const basic = { level: 1, xp: 0, max_hp: 100, hp: 100, max_rp: 0, rp: 0, strength: 10, intelligence: 10, vitality: 10 };
    const nameBytes = new TextEncoder().encode(name || `M${species}`);
    return this.document.transact(`Add experimental roster species ${species}`, bytes => {
      const offset = monster.offset, base = 0xb44 + monster.id * 100, view = this.document.view(bytes);
      bytes.fill(0, offset, offset + MONSTER_STRIDE);
      bytes.set(nameBytes, offset);
      bytes[offset + 19] = monster.id;
      bytes[offset + 20] = species;
      bytes[offset + 21] = room.map;
      view.setUint16(offset + 22, room.map, true); // current map at home, not in party
      view.setUint16(offset + 24, points, true);
      view.setInt16(offset + 26, 106, true); // audited home-spawn lower bounds
      view.setInt16(offset + 28, 170, true);
      view.setUint32(offset + 32, 0x1000, true); // occupied, no work/party transient flags
      bytes.set(block, base);
      const staged = Object.create(this.document); staged.data = bytes;
      staged.transact = (_label, edit) => { edit(bytes); return true; };
      const editor = new ExtendedSave(staged);
      const changes = source === undefined ? { ...basic, ...stats } : stats;
      // Validate copied blocks too; uninitialized NPC records are not templates.
      const values = { ...editor.stats('monster', monster.id), ...changes };
      for (const [key, spec] of Object.entries(STAT_FIELDS)) integer(values[key], spec.min, spec.max, spec.label);
      editor.setStats('monster', monster.id, changes);
    });
  }
}
