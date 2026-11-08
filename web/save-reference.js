import { integer, FLAGS_BITS } from './save-core.js';
import { RECIPE_BIT_BASE } from './extended-core.js';

export const RECIPE_FILES = {
  rf3RecipeAcce: 'Accessories', rf3RecipeArmor: 'Armor', rf3RecipeCookFry: 'Frying pan', rf3RecipeCookHandmade: 'Handmade food', rf3RecipeCookKnife: 'Knife', rf3RecipeCookMixer: 'Mixer', rf3RecipeCookOven: 'Oven', rf3RecipeCookPan: 'Pot', rf3RecipeCookSteamer: 'Steamer', rf3RecipeDrug: 'Chemistry', rf3RecipeFarm: 'Farm tools', rf3RecipeHat: 'Headgear', rf3RecipeShield: 'Shields', rf3RecipeShoes: 'Shoes', rf3RecipeWeaponA: 'Short swords', rf3RecipeWeaponB: 'Long swords', rf3RecipeWeaponC: 'Spears', rf3RecipeWeaponD: 'Axes / hammers', rf3RecipeWeaponK: 'Staves', rf3RecipeWeaponM: 'Dual blades', rf3RecipeWeaponN: 'Fists',
};

export function parseRecipes(input, filename) {
  const kind = Object.keys(RECIPE_FILES).find(key => `${key}.bin`.toLowerCase() === filename.toLowerCase());
  if (!kind) throw new Error('Choose a supported rf3Recipe*.bin table.');
  const bytes = new Uint8Array(input);
  if (bytes.length < 28 || String.fromCharCode(...bytes.subarray(0, 4)) !== 'NLCL') throw new Error('Expected an NLCL recipe table.');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const count = view.getUint32(24, true);
  if (view.getUint32(16, true) !== 1 || count < 1 || count > 1000 || view.getUint32(20, true) !== 28 + count * 20 || 28 + count * 20 > bytes.length) throw new Error('Invalid recipe table bounds.');
  const records = [];
  for (let index = 1; index < count; index++) {
    const offset = 28 + index * 20;
    const result = view.getUint16(offset, true);
    if (result) records.push({ kind, index, result, level: view.getUint16(offset + 14, true), bitOffset: RECIPE_BIT_BASE + view.getUint32(offset + 16, true) });
  }
  return { kind, records };
}

export class SaveReferences {
  constructor(local = null) { this.tables = new Map(); for (const table of local?.recipes || []) this.add(table); }
  add(table) {
    if (!Object.hasOwn(RECIPE_FILES, table.kind) || !Array.isArray(table.records) || table.records.length > 1000) throw new Error('Invalid recipe reference.');
    const records = table.records.map(record => Object.freeze({ kind: table.kind, index: integer(record.index, 1, 999, 'Recipe index'), result: integer(record.result, 1, 2047, 'Recipe result'), level: integer(record.level, 0, 65535, 'Recipe difficulty'), bitOffset: integer(record.bitOffset, RECIPE_BIT_BASE, FLAGS_BITS - 1, 'Recipe learned bit') }));
    const candidate = new Map(this.tables);
    candidate.set(table.kind, records);
    const seen = new Map();
    for (const recipe of [...candidate.values()].flat()) {
      const identity = `${recipe.kind}:${recipe.result}`;
      if (seen.has(recipe.bitOffset) && seen.get(recipe.bitOffset) !== identity) throw new Error('Unrelated recipes overlap; nothing was imported.');
      seen.set(recipe.bitOffset, identity);
    }
    this.tables = candidate;
  }
  recipes(kind = 'all') { return [...this.tables.values()].flat().filter(record => kind === 'all' || record.kind === kind); }
}
