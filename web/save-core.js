export const SAVE_SIZE = 140424;
export const SWITCH_SAVE_SIZE = 140416;
export const SYSTEM_SAVE_SIZE = 9304;
export const SYSTEM_FLAGS_OFFSET = 0x10;
export const SWITCH_CRC_END = SWITCH_SAVE_SIZE - 224;
export const CRC_START = 4;
export const CRC_LENGTH = 140196;
export const CRC_END = CRC_START + CRC_LENGTH;
export const FLAGS_OFFSET = 0x1e8c4;
export const FLAGS_BITS = 6656;
export const SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter'];
export const SCALARS = { day: 0x14, season: 0x18, year: 0x1c };
export const STORY_REGISTER = { name: 'REG_MAIN_SCENARIO', bitOffset: 0, width: 9 };
export const NUMBER_TYPES = {
  u8: { bytes: 1, getter: 'getUint8', setter: 'setUint8', min: 0, max: 255 },
  i8: { bytes: 1, getter: 'getInt8', setter: 'setInt8', min: -128, max: 127 },
  u16: { bytes: 2, getter: 'getUint16', setter: 'setUint16', min: 0, max: 65535 },
  i16: { bytes: 2, getter: 'getInt16', setter: 'setInt16', min: -32768, max: 32767 },
  u32: { bytes: 4, getter: 'getUint32', setter: 'setUint32', min: 0, max: 0xffffffff },
  i32: { bytes: 4, getter: 'getInt32', setter: 'setInt32', min: -2147483648, max: 2147483647 },
};
export const PLAYER_FIELDS = {
  lumber: { offset: 0x3c, type: 'i32', min: 0, max: 50000, label: 'Lumber' },
  material_stone: { offset: 0x40, type: 'i32', min: 0, max: 50000, label: 'Material stone' },
  fertilizer: { offset: 0x44, type: 'i32', min: 0, max: 50000, label: 'Fertilizer' },
  money: { offset: 0x4c, type: 'i32', min: 0, max: 2000000000, label: 'Money' },
  prince_points: { offset: 0x20710, type: 'i32', min: 0, max: 99999, label: 'Order points' },
  tourists: { offset: 0x20714, type: 'i32', min: 0, max: 99999999, label: 'Tourists' },
  max_hp: { offset: 0x54, type: 'i32', min: 1, max: 2147483647, label: 'Maximum health' },
  hp: { offset: 0x58, type: 'i32', min: 0, max: 2147483647, label: 'Current health' },
  max_rp: { offset: 0x5c, type: 'u16', min: 1, max: 65535, label: 'Maximum rune points' },
  rp: { offset: 0x5e, type: 'u16', min: 0, max: 65535, label: 'Current rune points' },
  strength: { offset: 0x60, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Strength' },
  intelligence: { offset: 0x64, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Intelligence' },
  vitality: { offset: 0x68, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Vitality' },
};
export const GENDER_OFFSET = 0x36;
export const APPEARANCE_FLAGS_OFFSET = 0x38;
export const APPEARANCE_OVERRIDE_OFFSET = 0x20740;
export const OUTFIT_OFFSET = 0x74;
export const OUTFIT_MASK = 0xfc0000;
export const DATING_CANDIDATES = [
  [1, 'Vishnal', 'male'], [5, 'Kiel', 'male'], [8, 'Dylas', 'male'],
  [9, 'Arthur', 'male'], [15, 'Doug', 'male'], [20, 'Leon', 'male'],
  [2, 'Clorica', 'female'], [4, 'Forte', 'female'], [7, 'Margaret', 'female'],
  [11, 'Xiao Pai', 'female'], [13, 'Amber', 'female'], [17, 'Dolce', 'female'],
].map(([id, name, gender]) => ({ id, name, gender }));
const SPOUSE_REGISTER = { bitOffset: 198, width: 5 };
export const BAG_OFFSET = 0x5bd8;
export const BAG_SLOTS = 60;
export const ITEM_RECORD_SIZE = 28;
export const INVENTORIES = {
  bag: { label: 'Bag', offset: BAG_OFFSET, slots: BAG_SLOTS },
  fridge: { label: 'Fridge', offset: 0x62a4, slots: 990 },
  storage: { label: 'Storage', offset: 0xceec, slots: 990 },
  weapons: { label: 'Weapon box', offset: 0x13b34, slots: 120 },
  armor: { label: 'Armor box', offset: 0x14854, slots: 120 },
};
export const SYSTEM_FLAGS = [
  { bit: 0, label: 'Ending / extra-orders unlock' },
  { bit: 2, label: 'Wedding recorded (system bit 2)' },
  { bit: 3, label: 'Wedding recorded (system bit 3)' },
  { bit: 4, label: 'Final-story marker (meaning incomplete)' },
  { bit: 5, label: 'Data-transfer order unlocked' },
];

export function saveLayout(input) {
  const bytes = new Uint8Array(input);
  if (bytes.length === SYSTEM_SAVE_SIZE) {
    if (String.fromCharCode(...bytes.subarray(0, 4)) !== 'RF4D') throw new Error('System saves require the RF4D signature.');
    return { kind: 'system', platform: 'shared', size: SYSTEM_SAVE_SIZE, crcOffset: 4, crcStart: 8, crcEnd: SYSTEM_SAVE_SIZE, protectedSize: 8 };
  }
  if (![SAVE_SIZE, SWITCH_SAVE_SIZE].includes(bytes.length)) throw new Error(`Unsupported save size: ${bytes.length.toLocaleString()} bytes. Expected PC ${SAVE_SIZE}, Switch ${SWITCH_SAVE_SIZE}, or system ${SYSTEM_SAVE_SIZE}.`);
  return { kind: 'slot', platform: bytes.length === SAVE_SIZE ? 'pc' : 'switch', size: bytes.length, crcOffset: 0, crcStart: 4, crcEnd: bytes.length - 224, protectedSize: 4 };
}

export function convertSlot(input, target, { experimental = false } = {}) {
  const bytes = new Uint8Array(input);
  const layout = saveLayout(bytes);
  if (layout.kind !== 'slot' || !['pc', 'switch'].includes(target)) throw new Error('Choose a PC or Switch slot conversion. System saves already share their container layout.');
  if (layout.platform === target) return bytes.slice();
  if (new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(0, true) !== crc32(bytes.subarray(4, layout.crcEnd))) throw new Error('Repair the source checksum before conversion.');
  if (!experimental) throw new Error('Acknowledge experimental conversion. Matching checksums do not verify every cross-platform field.');
  const source = new SaveDocument(bytes);
  if (!source.playerProfile || source.calendarIssues().length) throw new Error('Conversion requires recognized calendar and player values.');
  if (layout.platform === 'pc' && bytes.subarray(SWITCH_CRC_END, CRC_END).some(byte => byte !== 0)) throw new Error('PC-only eight-byte region is not empty. Conversion would discard data and has been blocked.');
  const output = new Uint8Array(target === 'pc' ? SAVE_SIZE : SWITCH_SAVE_SIZE);
  output.set(bytes.subarray(0, SWITCH_CRC_END));
  output.set(bytes.subarray(layout.crcEnd), output.length - 224);
  new DataView(output.buffer).setUint32(0, crc32(output.subarray(4, output.length - 224)), true);
  return output;
}

export function bagStackLimit(definition) {
  if (!definition) throw new Error('Read the item definition table before editing bag items.');
  const category = integer(definition.category, 0, 255, 'Item category');
  if (category === 55) throw new Error('Category placeholders cannot be created as bag items.');
  return integer(definition.max_stack, 0, 15, 'Definition stack limit') > 1 ? 9 : 1;
}

const crcTable = Uint32Array.from({ length: 256 }, (_, index) => {
  let value = index;
  for (let bit = 0; bit < 8; bit++) value = (value >>> 1) ^ ((value & 1) ? 0xedb88320 : 0);
  return value >>> 0;
});

export function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = (crc >>> 8) ^ crcTable[(crc ^ byte) & 255];
  return (crc ^ 0xffffffff) >>> 0;
}

export function integer(value, min, max, label = 'Value') {
  if (typeof value !== 'number' && typeof value !== 'string') throw new Error(`${label} must be a number.`);
  if (typeof value === 'string' && !value.trim()) throw new Error(`${label} is required.`);
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number < min || number > max) {
    throw new Error(`${label} must be a whole number from ${min} to ${max}.`);
  }
  return number;
}

export function hex(value, digits = 5) {
  return `0x${value.toString(16).toUpperCase().padStart(digits, '0')}`;
}

export function equalBytes(a, b) {
  return a.length === b.length && a.every((byte, index) => byte === b[index]);
}

function validateFlag(variable) {
  integer(variable.width, 1, 32, 'Bit width');
  integer(variable.bitOffset, 0, FLAGS_BITS - variable.width, 'Bit offset');
  if (variable.bitOffset < 4096 && variable.bitOffset + variable.width > 4096) {
    throw new Error('A field cannot cross the flag-zone boundary.');
  }
}

export function readFlag(bytes, variable) {
  validateFlag(variable);
  let value = 0;
  for (let i = 0; i < variable.width; i++) {
    const bit = variable.bitOffset + i;
    value = value * 2 + ((bytes[FLAGS_OFFSET + (bit >> 3)] >>> (bit & 7)) & 1);
  }
  return value;
}

export function writeFlag(bytes, variable, input) {
  validateFlag(variable);
  const value = integer(input, 0, 2 ** variable.width - 1, variable.name || 'Flag');
  for (let i = 0; i < variable.width; i++) {
    const bit = variable.bitOffset + i;
    const offset = FLAGS_OFFSET + (bit >> 3);
    const mask = 1 << (bit & 7);
    const set = Math.floor(value / 2 ** (variable.width - i - 1)) % 2;
    bytes[offset] = set ? bytes[offset] | mask : bytes[offset] & ~mask;
  }
}

export function parseEmdeb(input) {
  const bytes = new Uint8Array(input);
  if (bytes.length < 64 || String.fromCharCode(...bytes.slice(0, 4)) !== 'EMDb') {
    throw new Error('Choose the extracted emdeb.bin symbol table, not em.bin.');
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const count = view.getUint32(24, true);
  const first = view.getUint32(28, true) + 4;
  const namesBase = view.getUint32(52, true);
  if (!count || count > 4096 || first < 64 || first + count * 24 > namesBase || namesBase >= bytes.length) {
    throw new Error('Invalid symbol-table bounds. No symbols were loaded.');
  }
  const names = new Set();
  const used = new Set();
  const variables = [];
  for (let i = 0; i < count; i++) {
    const base = first + i * 24;
    const pointer = view.getUint32(base, true);
    const bitOffset = view.getUint32(base + 12, true);
    const width = (view.getUint32(base + 16, true) >>> 8) & 255;
    if (pointer < namesBase || pointer >= bytes.length) throw new Error('Invalid symbol-name pointer.');
    const end = bytes.indexOf(0, pointer);
    if (end < 0 || end - pointer > 256) throw new Error('Invalid symbol name.');
    const raw = bytes.subarray(pointer, end);
    if (raw.some(byte => byte > 127)) throw new Error('Expected an ASCII developer symbol.');
    const name = String.fromCharCode(...raw);
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) || names.has(name)) throw new Error('Invalid or duplicate developer symbol.');
    const variable = { name, bitOffset, width };
    validateFlag(variable);
    if (bitOffset + width > 4096) throw new Error('Developer symbols must stay in flag zone 1.');
    for (let bit = bitOffset; bit < bitOffset + width; bit++) {
      if (used.has(bit)) throw new Error('Overlapping developer symbols.');
      used.add(bit);
    }
    names.add(name);
    variables.push(variable);
  }
  return variables;
}

export class SaveDocument {
  constructor(input, name = 'rf4_s00.sav') {
    const bytes = new Uint8Array(input);
    Object.assign(this, saveLayout(bytes));
    this.original = bytes.slice();
    this.data = bytes.slice();
    this.name = name;
    this.undoStack = [];
    this.redoStack = [];
    this._exportedData = null;
    this.originalCrc = this.view(this.original).getUint32(this.crcOffset, true);
    this.originalComputedCrc = crc32(this.original.subarray(this.crcStart, this.crcEnd));
    this.crcValid = this.originalCrc === this.originalComputedCrc;
    this.playerProfile = this.kind === 'slot' && this.playerIssues(this.original).length === 0;
  }

  requireSlot() {
    if (this.kind !== 'slot') throw new Error('This operation requires a slot save, not rf4_sys.sav.');
  }

  gender(bytes = this.data) {
    this.requireSlot();
    return bytes[GENDER_OFFSET] === 0 ? 'male' : bytes[GENDER_OFFSET] === 1 ? 'female' : null;
  }

  appearance(bytes = this.data) {
    this.requireSlot();
    return { swapped: Boolean(this.readNumber(APPEARANCE_FLAGS_OFFSET, 'u32', bytes) & 1), override: this.readNumber(APPEARANCE_OVERRIDE_OFFSET, 'i32', bytes), outfit: (this.readNumber(OUTFIT_OFFSET, 'u32', bytes) & OUTFIT_MASK) >>> 18 };
  }

  genderCorrection(gender = 'keep', resetAppearance = false) {
    if (!['keep', 'original', 'male', 'female'].includes(gender)) throw new Error('Choose keep, original, male or female for gender export.');
    if (typeof resetAppearance !== 'boolean') throw new Error('Appearance reset must be a checkbox value.');
    if (gender === 'keep') {
      if (resetAppearance) throw new Error('Enable gender correction before resetting appearance.');
      return null;
    }
    this.requireSlot();
    const selected = gender === 'original' ? this.gender(this.original) : gender;
    if (!selected) throw new Error('Original gender is unrecognized. Choose male or female explicitly.');
    return { gender: selected, code: selected === 'female' ? 1 : 0, resetAppearance };
  }

  datingCleanup(gender) {
    this.requireSlot();
    if (!['male', 'female'].includes(gender)) throw new Error('Choose male or female before cleaning dating state.');
    const people = DATING_CANDIDATES.filter(person => person.gender === gender);
    const spouse = this.flag(SPOUSE_REGISTER);
    if (spouse && (!DATING_CANDIDATES.some(person => person.id === spouse) || people.some(person => person.id === spouse))) throw new Error('Dating cleanup cannot handle this spouse. Resolve marriage separately; family/event state will not be erased.');
    return people.map(person => {
      const offset = 0x1db40 + (person.id - 1) * 44;
      return { id: person.id, name: person.name, offset, dating: Boolean(this.readNumber(offset + 8, 'u32') & 0x400000), npcCallsPlayer: (gender === 'male' ? 23 : 70) + person.id, playerCallsNpc: (gender === 'male' ? 0 : 47) + person.id };
    });
  }

  systemFlag(bitInput, bytes = this.data) {
    if (this.kind !== 'system') throw new Error('Open rf4_sys.sav first.');
    const bit = integer(bitInput, 0, 31, 'System flag bit');
    return (this.view(bytes).getUint32(SYSTEM_FLAGS_OFFSET, true) >>> bit) & 1;
  }

  setSystemFlags(values) {
    if (this.kind !== 'system') throw new Error('Open rf4_sys.sav first.');
    const parsed = Object.entries(values).map(([bit, value]) => [integer(bit, 0, 31, 'System flag bit'), integer(value, 0, 1, 'System flag')]);
    return this.transact('System flags', next => {
      const view = this.view(next);
      let flags = view.getUint32(SYSTEM_FLAGS_OFFSET, true);
      for (const [bit, value] of parsed) flags = value ? flags | (1 << bit) : flags & ~(1 << bit);
      view.setUint32(SYSTEM_FLAGS_OFFSET, flags >>> 0, true);
    });
  }

  view(bytes = this.data) {
    return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  }

  get(name, bytes = this.data) {
    this.requireSlot();
    if (!(name in SCALARS)) throw new Error('Unknown calendar field.');
    return this.view(bytes).getUint32(SCALARS[name], true);
  }

  transact(label, mutate) {
    const next = this.data.slice();
    mutate(next);
    if (next.length !== this.data.length || !equalBytes(next.subarray(0, this.protectedSize), this.data.subarray(0, this.protectedSize))) {
      throw new Error('The checksum header cannot be edited directly.');
    }
    const patches = [];
    for (let offset = this.protectedSize; offset < next.length; offset++) {
      if (next[offset] !== this.data[offset]) patches.push({ offset, before: this.data[offset], after: next[offset] });
    }
    if (!patches.length) return false;
    this.undoStack.push({ label, patches });
    this.redoStack = [];
    this.data = next;
    return true;
  }

  setCalendar({ day, season, year }) {
    this.requireSlot();
    const values = {
      day: integer(day, 1, 30, 'Day'),
      season: integer(season, 0, 3, 'Season'),
      year: integer(year, 1, 0xffffffff, 'Year'),
    };
    return this.transact('Calendar', next => {
      const view = this.view(next);
      for (const [name, value] of Object.entries(values)) view.setUint32(SCALARS[name], value, true);
    });
  }

  flag(variable, bytes = this.data) {
    this.requireSlot();
    return readFlag(bytes, variable);
  }

  setFlag(variable, value) {
    this.requireSlot();
    return this.transact(variable.name, next => writeFlag(next, variable, value));
  }

  setFlags(entries, label = 'Progress flags') {
    this.requireSlot();
    if (!Array.isArray(entries) || entries.length > 4096) throw new Error('Expected a bounded list of flag edits.');
    const used = new Set();
    const parsed = entries.map(({ variable, value }) => {
      validateFlag(variable);
      for (let bit = variable.bitOffset; bit < variable.bitOffset + variable.width; bit++) {
        if (used.has(bit)) throw new Error('Progress edits overlap.');
        used.add(bit);
      }
      return { variable, value: integer(value, 0, 2 ** variable.width - 1, variable.name) };
    });
    return this.transact(label, next => { for (const { variable, value } of parsed) writeFlag(next, variable, value); });
  }

  patchBytes(offsetInput, text) {
    const offset = integer(offsetInput, this.protectedSize, this.size - 1, 'Offset');
    if (!/^[\da-fA-F]{2}(?:\s+[\da-fA-F]{2})*$/.test(text.trim())) {
      throw new Error('Use two-digit hex bytes separated by spaces, such as 09 00 00 00.');
    }
    const bytes = Uint8Array.from(text.trim().split(/\s+/), byte => parseInt(byte, 16));
    if (bytes.length > 256) throw new Error('Apply at most 256 bytes in one edit.');
    if (offset + bytes.length > this.size) throw new Error('The patch extends beyond the save.');
    return this.transact(`Bytes at ${hex(offset)}`, next => next.set(bytes, offset));
  }

  readNumber(offsetInput, type, bytes = this.data) {
    if (!Object.hasOwn(NUMBER_TYPES, type)) throw new Error('Unknown integer type.');
    const spec = NUMBER_TYPES[type];
    const offset = integer(offsetInput, 0, this.size - spec.bytes, 'Save offset');
    return this.view(bytes)[spec.getter](offset, true);
  }

  setNumber(offsetInput, type, input) {
    if (!Object.hasOwn(NUMBER_TYPES, type)) throw new Error('Unknown integer type.');
    const spec = NUMBER_TYPES[type];
    const offset = integer(offsetInput, this.protectedSize, this.size - spec.bytes, 'Save offset');
    const value = integer(input, spec.min, spec.max, type);
    return this.transact(`${type} at ${hex(offset)}`, next => this.view(next)[spec.setter](offset, value, true));
  }

  player(name, bytes = this.data) {
    this.requireSlot();
    if (!Object.hasOwn(PLAYER_FIELDS, name)) throw new Error('Unknown player field.');
    const spec = PLAYER_FIELDS[name];
    const value = this.readNumber(spec.offset, spec.type, bytes);
    return spec.bits === 24 ? value & 0xffffff : value;
  }

  playerIssues(bytes = this.data) {
    const issues = [];
    for (const [name, spec] of Object.entries(PLAYER_FIELDS)) {
      const value = this.player(name, bytes);
      if (value < spec.min || value > spec.max) issues.push(`${spec.label} is outside its stored range.`);
    }
    if (this.player('hp', bytes) > this.player('max_hp', bytes)) issues.push('Current health cannot exceed maximum health.');
    if (this.player('rp', bytes) > this.player('max_rp', bytes)) issues.push('Current rune points cannot exceed the maximum.');
    return issues;
  }

  setPlayer(values) {
    this.requireSlot();
    const parsed = Object.fromEntries(Object.entries(values).map(([name, input]) => {
      if (!Object.hasOwn(PLAYER_FIELDS, name)) throw new Error('Unknown player field.');
      const spec = PLAYER_FIELDS[name];
      return [name, integer(input, spec.min, spec.max, spec.label)];
    }));
    return this.transact('Player attributes', next => {
      const view = this.view(next);
      for (const [name, value] of Object.entries(parsed)) {
        const spec = PLAYER_FIELDS[name];
        const result = spec.bits === 24 ? ((view.getUint32(spec.offset, true) & 0xff000000) | value) >>> 0 : value;
        view[NUMBER_TYPES[spec.type].setter](spec.offset, result, true);
      }
      if (('hp' in parsed || 'max_hp' in parsed) && this.player('hp', next) > this.player('max_hp', next)) throw new Error('Current health cannot exceed maximum health.');
      if (('rp' in parsed || 'max_rp' in parsed) && this.player('rp', next) > this.player('max_rp', next)) throw new Error('Current rune points cannot exceed the maximum.');
    });
  }

  bagSlot(slotInput, bytes = this.data) {
    return this.inventorySlot('bag', slotInput, bytes);
  }

  inventorySlot(container, slotInput, bytes = this.data) {
    this.requireSlot();
    if (!Object.hasOwn(INVENTORIES, container)) throw new Error('Unknown saved container.');
    const spec = INVENTORIES[container];
    const slot = integer(slotInput, 0, spec.slots - 1, `${spec.label} slot`);
    const offset = spec.offset + slot * ITEM_RECORD_SIZE;
    const header = this.view(bytes).getUint16(offset, true);
    const id = header & 0x7ff;
    const quantity = (header >>> 11) & 15;
    const levels = id ? Array.from({ length: Math.max(1, Math.min(quantity, 9)) }, (_, i) => bytes[offset + 4 + i] + 1) : [];
    return { slot, offset, id, quantity, level: levels[0] || 1, levels, mixedLevels: levels.some(level => level !== levels[0]), headerFlag: Boolean(header & 0x8000) };
  }

  bagItems(bytes = this.data) { return Array.from({ length: BAG_SLOTS }, (_, slot) => this.bagSlot(slot, bytes)); }
  inventoryItems(container, bytes = this.data) {
    this.requireSlot();
    if (!Object.hasOwn(INVENTORIES, container)) throw new Error('Unknown saved container.');
    return Array.from({ length: INVENTORIES[container].slots }, (_, slot) => this.inventorySlot(container, slot, bytes));
  }

  setBagItem(slotInput, changes, definition) {
    return this.setInventoryItem('bag', slotInput, changes, definition);
  }

  setInventoryItem(container, slotInput, changes, definition) {
    const current = this.inventorySlot(container, slotInput);
    const slot = current.slot;
    const id = integer(changes.id, 0, 0x7ff, 'Item ID');
    const maxStack = id ? bagStackLimit(definition) : 0;
    const quantity = integer(changes.quantity, id ? 1 : 0, maxStack, 'Quantity');
    const level = changes.level === undefined ? undefined : integer(changes.level, 1, 10, 'Item level');
    return this.transact(`${INVENTORIES[container].label} slot ${slot + 1}`, next => {
      const offset = current.offset;
      const view = this.view(next);
      if (!id) { next.fill(0, offset, offset + ITEM_RECORD_SIZE); return; }
      if (id !== current.id) {
        next.fill(0, offset, offset + ITEM_RECORD_SIZE);
        view.setUint16(offset, id | (quantity << 11), true);
        next.fill((level || 1) - 1, offset + 4, offset + 4 + maxStack);
        return;
      }
      const header = view.getUint16(offset, true);
      view.setUint16(offset, (header & 0x87ff) | (quantity << 11), true);
      if (level !== undefined) next.fill(level - 1, offset + 4, offset + 4 + maxStack);
      else if (quantity > current.quantity) {
        const storedLevel = integer(next[offset + 4], 0, 9, 'Existing item level');
        next.fill(storedLevel, offset + 4 + current.quantity, offset + 4 + quantity);
      }
    });
  }

  undo() {
    const edit = this.undoStack.pop();
    if (!edit) return false;
    for (const patch of edit.patches) this.data[patch.offset] = patch.before;
    this.redoStack.push(edit);
    return true;
  }

  redo() {
    const edit = this.redoStack.pop();
    if (!edit) return false;
    for (const patch of edit.patches) this.data[patch.offset] = patch.after;
    this.undoStack.push(edit);
    return true;
  }

  reset() {
    return this.transact('Restore original', next => next.set(this.original));
  }

  get changedBytes() {
    let count = 0;
    for (let offset = this.protectedSize; offset < this.data.length; offset++) count += this.data[offset] !== this.original[offset];
    return count;
  }

  get dirty() {
    return !equalBytes(this.data, this.original);
  }

  // Payload lifecycle, independent of history, drafts and export-only options.
  // Before the first export compare with the import; afterwards use the last
  // export checkpoint, even when undo/reset has restored the imported bytes.
  get exportState() {
    if (this._exportedData === null) return this.dirty ? 'unexported' : 'original';
    return equalBytes(this.data, this._exportedData) ? 'exported' : 'unexported';
  }

  // Call only after a successful native write (or a browser download request).
  // build() is read-only and never acknowledges an export.
  markExported() {
    this._exportedData = this.data.slice();
    return 'exported';
  }

  changes() {
    const ranges = [];
    let range;
    for (let offset = this.protectedSize; offset < this.data.length; offset++) {
      if (this.data[offset] === this.original[offset]) { range = undefined; continue; }
      if (!range) {
        range = { offset, before: [], after: [] };
        ranges.push(range);
      }
      range.before.push(this.original[offset]);
      range.after.push(this.data[offset]);
    }
    return ranges;
  }

  calendarIssues() {
    if (this.kind === 'system') return [];
    const issues = [];
    if (this.get('day') < 1 || this.get('day') > 30) issues.push('Day must be 1–30.');
    if (this.get('season') > 3) issues.push('Season must be 0–3.');
    if (this.get('year') < 1) issues.push('Year must be at least 1.');
    return issues;
  }

  build({ repair = false, platform = this.platform, experimental = false, gender = 'keep', resetAppearance = false, resetDating = false } = {}) {
    if (!this.crcValid && !repair) throw new Error('Acknowledge checksum repair before exporting this damaged save.');
    const issues = this.calendarIssues();
    if (issues.length) throw new Error(issues.join(' '));
    const playerIssues = this.playerProfile ? this.playerIssues() : [];
    if (playerIssues.length) throw new Error(playerIssues.join(' '));
    const correction = this.genderCorrection(gender, resetAppearance);
    if (typeof resetDating !== 'boolean') throw new Error('Dating cleanup must be a checkbox value.');
    if (resetDating && !correction) throw new Error('Enable gender correction before cleaning dating state.');
    const dating = resetDating ? this.datingCleanup(correction.gender) : [];
    const output = this.data.slice();
    if (correction) {
      output[GENDER_OFFSET] = correction.code;
      if (correction.resetAppearance) {
        const view = this.view(output);
        view.setUint32(APPEARANCE_FLAGS_OFFSET, (view.getUint32(APPEARANCE_FLAGS_OFFSET, true) & ~1) >>> 0, true);
        view.setUint32(OUTFIT_OFFSET, (view.getUint32(OUTFIT_OFFSET, true) & ~OUTFIT_MASK) >>> 0, true);
        view.setInt32(APPEARANCE_OVERRIDE_OFFSET, 0, true);
      }
    }
    const view = this.view(output);
    for (const person of dating) {
      view.setUint32(person.offset + 8, (view.getUint32(person.offset + 8, true) & ~0x400000) >>> 0, true);
      output[person.offset + 12] = person.npcCallsPlayer;
      view.setUint32(person.offset + 20, (view.getUint32(person.offset + 20, true) & ~0x7f80 | person.playerCallsNpc << 7) >>> 0, true);
    }
    this.view(output).setUint32(this.crcOffset, crc32(output.subarray(this.crcStart, this.crcEnd)), true);
    if (platform === this.platform) return output;
    return convertSlot(output, platform, { experimental });
  }
}

export function createDemo() {
  const bytes = new Uint8Array(SAVE_SIZE);
  const view = new DataView(bytes.buffer);
  view.setUint32(SCALARS.day, 9, true);
  view.setUint32(SCALARS.season, 0, true);
  view.setUint32(SCALARS.year, 1, true);
  writeFlag(bytes, STORY_REGISTER, 104);
  for (const [name, value] of Object.entries({ money: 200, max_hp: 25, hp: 25, max_rp: 56, rp: 56, strength: 5, intelligence: 5, vitality: 4 })) {
    const spec = PLAYER_FIELDS[name];
    view[NUMBER_TYPES[spec.type].setter](spec.offset, value, true);
  }
  for (const [slot, id, quantity] of [[0, 328, 1], [1, 559, 1], [2, 753, 9], [3, 753, 4]]) view.setUint16(BAG_OFFSET + slot * ITEM_RECORD_SIZE, id | (quantity << 11), true);
  view.setUint32(0, crc32(bytes.subarray(CRC_START, CRC_END)), true);
  return new SaveDocument(bytes, 'Demo · synthetic save');
}
