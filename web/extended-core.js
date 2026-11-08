import { integer, FLAGS_BITS, readFlag, writeFlag } from './save-core.js';
import { SAVE_METADATA } from './save-metadata.js';

export const SKILL_OFFSET = 0x5964;
export const SKILL_NAMES = ['Short sword', 'Long sword', 'Spear', 'Axe / hammer', 'Dual blades', 'Fist', 'Fire', 'Water', 'Earth', 'Wind', 'Light', 'Dark', 'Love', 'Farming', 'Logging', 'Mining', 'Fishing', 'Cooking', 'Forging', 'Chemistry', 'Crafting', 'Searching', 'Walking', 'Sleeping', 'Eating', 'Defense', 'Resist poison', 'Resist seal', 'Resist paralysis', 'Resist sleep', 'Resist fatigue', 'Resist cold', 'Resist knockout', 'Bathing', 'Taming', 'Throwing', 'Leadership', 'Bartering'];
export const SKILLS = SKILL_NAMES.map((name, id) => ({ id, name, max: id >= 17 && id <= 20 || id >= 26 && id <= 32 ? 99 : 999, group: id < 6 ? 'Weapons' : id < 13 ? 'Magic' : id < 17 ? 'Farm and field' : id < 21 ? 'Crafting' : id >= 26 && id <= 32 ? 'Resistances' : 'Life and other skills' }));
export const PEOPLE_NAMES = ['Player', 'Vishnal', 'Clorica', 'Volkanon', 'Forte', 'Kiel', 'Bado', 'Margaret', 'Dylas', 'Arthur', 'Porcoline', 'Xiao Pai', 'Lin Fa', 'Amber', 'Illuminata', 'Doug', 'Blossom', 'Dolce', 'Jones', 'Nancy', 'Leon', 'Ventuswill', 'Son', 'Daughter', 'Barrett', 'Raven', 'Mistress Trupin'];
export const FRIEND_THRESHOLDS = [0, 16, 42, 83, 140, 226, 322, 429, 704, 1009, 1345];
export const MONSTER_THRESHOLDS = [0, 8, 20, 36, 56, 80, 108, 140, 176, 212, 255];
export const MONSTER_OFFSET = 0x1bdb0;
export const MONSTER_COUNT = 200;
export const MONSTER_STRIDE = 36;
export const RECIPE_BIT_BASE = 4096 + 0x426;
export const STAT_FIELDS = {
  level: { offset: 24, type: 'u16', min: 1, max: 65530, label: 'Combat level' },
  xp: { offset: 28, type: 'u32', min: 0, max: 0xffffffff, label: 'Experience' },
  max_hp: { offset: 0, type: 'i32', min: 1, max: 0x7fffffff, label: 'Maximum health' },
  hp: { offset: 4, type: 'i32', min: 0, max: 0x7fffffff, label: 'Current health' },
  max_rp: { offset: 8, type: 'u16', min: 0, max: 65535, label: 'Maximum rune points' },
  rp: { offset: 10, type: 'u16', min: 0, max: 65535, label: 'Current rune points' },
  strength: { offset: 12, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Strength' },
  intelligence: { offset: 16, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Intelligence' },
  vitality: { offset: 20, type: 'u32', bits: 24, min: 1, max: 0xffffff, label: 'Vitality' },
};
const RESULT_LABELS = { SYUKKA: 'First shipment', DATE: 'First date', FISH: 'First fish caught', FMON: 'First monster tamed', SICK: 'First cold', BATH: 'First bath', MONEY: 'Savings milestone', LOVE_ALL10: 'Everyone reached friendship 10', MAME: 'Bean toss', MOKO: 'Wooly festival', SP_FISHING: 'Spring fishing', SU_FISHING: 'Summer fishing', AU_FISHING: 'Autumn fishing', WI_FISHING: 'Winter fishing', EAT: 'Eating contest', MATO: 'Target contest', YUKI: 'Snowball contest', SP_CROP: 'Spring harvest', SU_CROP: 'Summer harvest', AU_CROP: 'Autumn harvest', WI_CROP: 'Winter harvest', QUIZ: 'Quiz contest', PET: 'Buddy battle', COOK: 'Cooking contest', SMITH: 'Crafting contest' };
export const TROPHIES = SAVE_METADATA.symbols.filter(v => /^(FLG_RESULT_|REG_RESULT_FES_)/.test(v.name)).map(v => ({ ...v, label: RESULT_LABELS[v.name.replace(/^(FLG_RESULT_|REG_RESULT_FES_)/, '')] || v.description }));

export function friendshipLevel(points) {
  integer(points, 0, 0x333e71, 'Friendship points');
  if (points > 1345) return Math.min(10000, Math.floor((points + 2015) / 336));
  return FRIEND_THRESHOLDS.findLastIndex(value => value <= points);
}

export function friendshipPoints(level) {
  const n = integer(level, 0, 10000, 'Friendship level');
  return n <= 10 ? FRIEND_THRESHOLDS[n] : n * 336 - 2015;
}

export function monsterFriendshipLevel(points) {
  integer(points, 0, 65535, 'Monster friendship points');
  return points > 255 ? Math.min(1000, 10 + Math.floor((points - 255) / 64)) : MONSTER_THRESHOLDS.findLastIndex(value => value <= points);
}

export function monsterFriendshipPoints(level) {
  const n = integer(level, 0, 1000, 'Monster friendship level');
  return n <= 10 ? MONSTER_THRESHOLDS[n] : 255 + (n - 10) * 64;
}

export class ExtendedSave {
  constructor(document) { this.document = document; }
  slot() { this.document.requireSlot(); }
  skill(idInput, bytes = this.document.data) {
    this.slot();
    const id = integer(idInput, 0, SKILLS.length - 1, 'Skill');
    const offset = SKILL_OFFSET + id * 8;
    return { ...SKILLS[id], offset, level: this.document.readNumber(offset, 'u16', bytes), xp: this.document.readNumber(offset + 4, 'u32', bytes) };
  }
  setSkill(id, changes) {
    const skill = this.skill(id);
    const values = {};
    for (const [key, input] of Object.entries(changes)) {
      if (!['level', 'xp'].includes(key)) throw new Error('Unknown skill field.');
      values[key] = integer(input, 0, key === 'level' ? skill.max : 0xffffff, key);
    }
    return this.document.transact(skill.name, bytes => {
      const view = this.document.view(bytes);
      if (values.level !== undefined) view.setUint16(skill.offset, values.level, true);
      if (values.xp !== undefined) view.setUint32(skill.offset + 4, values.xp, true);
    });
  }
  friendship(idInput, bytes = this.document.data) {
    this.slot();
    const id = integer(idInput, 1, 25, 'Person');
    const guest = id >= 24;
    const offset = guest ? 0x1df34 + (id - 24) * 8 + 4 : 0x1db40 + (id - 1) * 44;
    const points = this.document.readNumber(offset, guest ? 'u16' : 'i32', bytes);
    return { id, name: PEOPLE_NAMES[id], offset, points, level: guest ? Math.min(10000, points >>> 2) : points >= 0 && points <= 0x333e71 ? friendshipLevel(points) : null, guest };
  }
  setFriendship(id, level) {
    const person = this.friendship(id);
    const n = integer(level, 0, 10000, 'Friendship level');
    return this.document.transact(`${person.name} friendship`, bytes => {
      const view = this.document.view(bytes);
      if (person.guest) view.setUint16(person.offset, n * 4 | person.points & 3, true);
      else view.setInt32(person.offset, friendshipPoints(n), true);
    });
  }
  monster(idInput, bytes = this.document.data) {
    this.slot();
    const id = integer(idInput, 0, MONSTER_COUNT - 1, 'Monster slot');
    const offset = MONSTER_OFFSET + id * MONSTER_STRIDE;
    const flags = this.document.readNumber(offset + 32, 'u32', bytes);
    const nameBytes = bytes.subarray(offset, offset + 19);
    const end = nameBytes.indexOf(0);
    const name = new TextDecoder().decode(nameBytes.subarray(0, end < 0 ? nameBytes.length : end));
    const points = this.document.readNumber(offset + 24, 'u16', bytes);
    return { id, offset, name, species: bytes[offset + 20], occupied: Boolean(flags & 0x1000), points, friendship: monsterFriendshipLevel(points), barn: bytes[offset + 21], flags };
  }
  monsters(bytes = this.document.data) { return Array.from({ length: MONSTER_COUNT }, (_, id) => this.monster(id, bytes)); }
  setMonsterFriendship(id, level) {
    const monster = this.monster(id);
    if (!monster.occupied) throw new Error('Edit an existing tamed monster; this does not create or tame monsters.');
    const points = monsterFriendshipPoints(level);
    return this.document.transact(`${monster.name || `Monster ${id + 1}`} friendship`, bytes => this.document.view(bytes).setUint16(monster.offset + 24, points, true));
  }
  setMonster(id, { stats = {}, friendship } = {}) {
    const monster = this.monster(id);
    if (!monster.occupied) throw new Error('Select an existing tamed monster.');
    return this.document.transact(`${monster.name || `Monster ${id + 1}`} values`, bytes => {
      const staged = Object.create(this.document);
      staged.data = bytes;
      staged.transact = (_label, change) => { change(bytes); return true; };
      const editor = new ExtendedSave(staged);
      if (Object.keys(stats).length) editor.setStats('monster', id, stats);
      if (friendship !== undefined) editor.setMonsterFriendship(id, friendship);
    });
  }
  statsOffset(kind, index) {
    this.slot();
    if (kind === 'person') return 0xb8 + integer(index, 1, 26, 'Person') * 100;
    if (kind === 'monster') {
      const monster = this.monster(index);
      if (!monster.occupied) throw new Error('Select an existing tamed monster.');
      return 0xb44 + monster.id * 100;
    }
    throw new Error('Choose person or monster stats.');
  }
  stats(kind, index, bytes = this.document.data) {
    const base = this.statsOffset(kind, index);
    return Object.fromEntries(Object.entries(STAT_FIELDS).map(([key, spec]) => {
      const value = this.document.readNumber(base + spec.offset, spec.type, bytes);
      return [key, spec.bits ? value & 0xffffff : value];
    }));
  }
  setStats(kind, index, changes) {
    const base = this.statsOffset(kind, index);
    const parsed = Object.fromEntries(Object.entries(changes).map(([key, input]) => {
      if (!Object.hasOwn(STAT_FIELDS, key)) throw new Error('Unknown actor-stat field.');
      const spec = STAT_FIELDS[key];
      return [key, integer(input, spec.min, spec.max, spec.label)];
    }));
    return this.document.transact(`${kind} ${index} base stats`, bytes => {
      const view = this.document.view(bytes);
      for (const [key, value] of Object.entries(parsed)) {
        const spec = STAT_FIELDS[key];
        const offset = base + spec.offset;
        const packed = spec.bits ? ((view.getUint32(offset, true) & 0xff000000) | value) >>> 0 : value;
        if (spec.type === 'i32') view.setInt32(offset, packed, true);
        else if (spec.type === 'u32') view.setUint32(offset, packed, true);
        else view.setUint16(offset, packed, true);
      }
      const stats = this.stats(kind, index, bytes);
      if (stats.hp > stats.max_hp || stats.rp > stats.max_rp) throw new Error('Current health / rune points cannot exceed the maxima.');
    });
  }
  trophy(name, bytes = this.document.data) {
    this.slot();
    const field = TROPHIES.find(v => v.name === name);
    if (!field) throw new Error('Unknown trophy / result record.');
    return this.document.flag(field, bytes);
  }
  setTrophy(name, value) {
    this.trophy(name);
    const field = TROPHIES.find(v => v.name === name);
    return this.document.setFlags([{ variable: field, value }], field.label);
  }
  recipe(recipe, bytes = this.document.data) {
    this.slot();
    const bit = integer(recipe.bitOffset, RECIPE_BIT_BASE, FLAGS_BITS - 1, 'Recipe bit');
    return Boolean(readFlag(bytes, { bitOffset: bit, width: 1 }));
  }
  setRecipes(recipes, known) {
    this.slot();
    if (typeof known !== 'boolean' || !Array.isArray(recipes) || !recipes.length || recipes.length > 1498) throw new Error('Choose a bounded recipe list and learned state.');
    const bits = new Set();
    for (const recipe of recipes) { this.recipe(recipe); if (bits.has(recipe.bitOffset)) throw new Error('Duplicate recipe bit.'); bits.add(recipe.bitOffset); }
    return this.document.transact(known ? 'Learn recipes' : 'Forget recipes', bytes => {
      for (const bitOffset of bits) writeFlag(bytes, { bitOffset, width: 1 }, Number(known));
    });
  }
}
