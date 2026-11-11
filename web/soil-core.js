// PC serializer 0x7DF09..0x7DF57 / loader 0x7FAD0..0x7FB08.
// Soil records are NOT the adjacent 12-byte crop records. Units below stay raw.
import { integer } from './save-core.js';

export const SOIL_OFFSET = 0x1aeb4;
export const SOIL_STRIDE = 16;
export const SOIL_FIELDS = [
  ['growth', 'Growth boost (raw 0–127)', 4, 7],
  ['yield', 'Yield magnitude (raw 0–1,023)', 11, 10],
  ['yieldNegative', 'Yield sign bit', 21, 1],
  ['quality', 'Quality magnitude (raw 0–511)', 22, 9],
  ['qualityNegative', 'Quality sign bit', 31, 1],
  ['size', 'Size magnitude (raw 0–511)', 32, 9],
  ['sizeNegative', 'Size sign bit', 41, 1],
  ['defense', 'Soil defense (raw 0–63)', 42, 6],
  ['health', 'Soil health (raw 0–255)', 48, 8],
  ['yieldLevel', 'Base yield level (raw 0–15)', 68, 4],
  ['qualityLevel', 'Base quality level (raw 0–15)', 72, 4],
  ['sizeLevel', 'Base size level (raw 0–15)', 76, 4],
  ['overallXp', 'Overall progress (raw 0–127)', 81, 7],
  ['speedXp', 'Speed progress (raw 0–127)', 89, 7],
  ['yieldXp', 'Yield progress (raw 0–127)', 97, 7],
  ['qualityXp', 'Quality progress (raw 0–127)', 105, 7],
  ['sizeXp', 'Size progress (raw 0–127)', 113, 7],
  ['overallLevel', 'Overall level (raw 0–15)', 120, 4],
  ['speedLevel', 'Base speed level (raw 0–15)', 124, 4],
].map(([key, label, bit, width]) => ({ key, label, bit, width, min: 0, max: 2 ** width - 1 }));
// Maximize magnitudes, never the negative sign bits. These remain raw limits.
export const SOIL_MAXIMUM = Object.fromEntries(SOIL_FIELDS.map(field => [field.key, field.key.endsWith('Negative') ? 0 : field.max]));
export const SOIL_FARMS = ['Center field', 'Bottom-left field', 'Bottom-right field', 'Top-left field', 'Top-right field', 'Spring field', 'Summer field', 'Autumn field', 'Winter field'].map((name, id) => ({ id, name, patches: id < 5 ? Array.from({ length: 18 }, (_, i) => i) : id === 5 ? [0,1,2,3,4,5,6,7] : id === 6 ? [0,1,2,3] : id === 7 ? [0,1,3,4,6,7] : Array.from({ length: 12 }, (_, i) => i) }));

function location(farmInput, patchInput) {
  const farm = SOIL_FARMS[integer(farmInput, 0, 8, 'Farm')];
  const patch = integer(patchInput, 0, 17, 'Soil patch');
  if (!farm.patches.includes(patch)) throw new Error('This soil patch is unused on the selected field.');
  return SOIL_OFFSET + (farm.id * 18 + patch) * SOIL_STRIDE;
}

function read(bytes, offset, field) {
  let value = 0;
  for (let i = 0; i < field.width; i++) value += ((bytes[offset + ((field.bit + i) >> 3)] >> ((field.bit + i) & 7)) & 1) * 2 ** i;
  return value;
}

export class SoilEditor {
  constructor(document) { this.document = document; }
  values(farm, patch, bytes = this.document.data) {
    this.document.requireSlot();
    const offset = location(farm, patch);
    return { offset, values: Object.fromEntries(SOIL_FIELDS.map(field => [field.key, read(bytes, offset, field)])) };
  }
  apply(farm, patch, changes, all = false) {
    this.document.requireSlot();
    if (typeof all !== 'boolean') throw new Error('All-patches selection must be boolean.');
    const first = location(farm, patch);
    const fields = Object.entries(changes).map(([key, input]) => {
      const field = SOIL_FIELDS.find(field => field.key === key);
      if (!field) throw new Error('Unknown soil field.');
      return { ...field, value: integer(input, 0, field.max, field.label) };
    });
    const offsets = all ? SOIL_FARMS[Number(farm)].patches.map(id => location(farm, id)) : [first];
    return this.document.transact('Soil values (raw packed fields)', bytes => {
      for (const offset of offsets) for (const field of fields) for (let i = 0; i < field.width; i++) {
        const address = offset + ((field.bit + i) >> 3), mask = 1 << ((field.bit + i) & 7);
        bytes[address] = Math.floor(field.value / 2 ** i) % 2 ? bytes[address] | mask : bytes[address] & ~mask;
      }
    });
  }
}
