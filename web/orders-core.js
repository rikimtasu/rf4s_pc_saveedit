// CT v12.3 RF4D+2A774..2A798 and v13 ExpGainPtr cross-check.
// The persisted order block is save+2071C; these are NOT GameFlags bits.
import { integer } from './save-core.js';

export const ORDER_FIELDS = [
  { key: 'enemyLevel', label: 'Enemy level increase (0–10)', offset: 0x2072c, min: 0, max: 10 },
  { key: 'noExp', label: 'Disable combat EXP', offset: 0x2071f, bit: 3 },
  { key: 'noSkillExp', label: 'Disable skill EXP', offset: 0x2071f, bit: 4 },
  { key: 'noTownEvents', label: 'Disable town events', offset: 0x2071e, bit: 5 },
  { key: 'showEnemyLevel', label: 'Show enemy levels', offset: 0x2071f, bit: 5 },
  { key: 'showEnemyHp', label: 'Show enemy HP', offset: 0x2071f, bit: 6 },
  { key: 'appearance', label: 'Appearance order (reload required)', offset: 0x20740, type: 'i32', min: 0, max: 9999 },
];
export const ORDER_APPEARANCES = [
  { id: 0, name: 'Default main character' }, { id: 9999, name: 'Opposite-gender appearance (dialogue unchanged)' },
  ...Array.from({ length: 20 }, (_, i) => ({ id: i + 1 })),
  ...[24, 25, 27, 28, 34, 35, 239, 309].map(id => ({ id })),
];

export class OrdersEditor {
  constructor(document) { this.document = document; }
  values() {
    this.document.requireSlot();
    return Object.fromEntries(ORDER_FIELDS.map(field => {
      const raw = this.document.readNumber(field.offset, field.type || 'u8');
      return [field.key, field.bit === undefined ? raw : (raw >> field.bit) & 1];
    }));
  }
  apply(changes) {
    this.document.requireSlot();
    const fields = Object.entries(changes).map(([key, input]) => {
      const field = ORDER_FIELDS.find(entry => entry.key === key);
      if (!field) throw new Error('Unknown extra order field.');
      const value = integer(input, field.min || 0, field.max === undefined ? 1 : field.max, field.label);
      if (key === 'appearance' && !ORDER_APPEARANCES.some(entry => entry.id === value)) throw new Error('Choose a supported appearance order.');
      return { ...field, value };
    });
    return this.document.transact('Extra orders', bytes => {
      for (const field of fields) {
        if (field.bit !== undefined) {
          const mask = 1 << field.bit;
          bytes[field.offset] = (bytes[field.offset] & ~mask) | (field.value ? mask : 0);
        } else this.document.view(bytes)[field.type === 'i32' ? 'setInt32' : 'setUint8'](field.offset, field.value, true);
      }
    });
  }
}
