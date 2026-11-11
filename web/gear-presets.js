// Curated staff builds, not a final-stat optimizer. See docs/order-soil-gear-shortcuts.md.
import { editInventoryItem, equipmentItem } from './item-details.js';

const defensiveCraft = [131, 62, 62]; // Object X, Mealy Apple, Mealy Apple
const magicUpgrades = [894, 933, 894, 932, 980, 963, 909, 884, 567];
const cores = [921, 922, 923, 924];
const offenseUpgrades = [894, 933, 894, 932, 980, ...cores];
const entry = (role, id, category, craft, upgrades) => ({ role, id, category, craft, upgrades });
export const GEAR_PRESETS = [
  { id: 'staff-balanced', name: 'Balanced optimized staff gear', items: [
    entry('Staff', 501, 24, [894, 894, 894], magicUpgrades),
    entry('Shield', 595, 33, defensiveCraft, [62, 131, 894, 933, 980, ...cores]),
    entry('Armor', 749, 37, [894, 894, 894], offenseUpgrades),
    // Clear Object X before positive cloth/fins/cores: never invert protection.
    entry('Headgear', 706, 35, defensiveCraft, [62, 131, 971, 933, 894, ...cores]),
    entry('Shoes', 729, 36, [725, 719, 723], [876, 933, 131, 62, 62, ...cores]),
    entry('Accessory', 665, 34, [626, 662, 661], [...cores, 894, 933, 894, 932, 980]),
  ] },
  { id: 'staff-damage', name: 'Maximum-damage optimized staff gear', items: [
    entry('Staff', 501, 24, [894, 894, 894], magicUpgrades),
    entry('Shield', 595, 33, [894, 894, 894], offenseUpgrades),
    entry('Armor', 749, 37, [894, 894, 894], offenseUpgrades),
    entry('Headgear', 706, 35, [894, 894, 894], offenseUpgrades),
    entry('Shoes', 729, 36, [725, 719, 723], offenseUpgrades),
    entry('Accessory', 665, 34, [626, 662, 674], offenseUpgrades),
  ] },
];

function presetFor(id) {
  const preset = GEAR_PRESETS.find(entry => entry.id === id);
  if (!preset) throw new Error('Unknown gear preset.');
  return preset;
}

export function gearPreset(id, catalog) {
  const preset = presetFor(id);
  const items = preset.items.map(item => {
    const definition = catalog.bagDefinition(item.id);
    if (!equipmentItem(definition) || definition.category !== item.category || !catalog.record('equipment', item.id)) throw new Error('Gear presets require matching item, equipment and upgrade tables.');
    for (const attached of [...item.craft, ...item.upgrades]) {
      const material = catalog.bagDefinition(attached);
      if (attached > 1023 || material.category === 55 || !catalog.record('upgrade', attached)) throw new Error('Gear presets require matching item, equipment and upgrade tables.');
      if (equipmentItem(material) && !catalog.record('equipment', attached)) throw new Error('Gear presets require matching item, equipment and upgrade tables.');
    }
    return { ...item, name: catalog.name(item.id), craft: item.craft.map(id => ({ id, name: catalog.name(id) })), upgrades: item.upgrades.map(id => ({ id, name: catalog.name(id) })) };
  });
  return { id, name: preset.name, items, level: 10, totalLevel: 150, rarityBonus: 200, exactFinalStats: false,
    source: 'https://gamefaqs.gamespot.com/boards/258612-rune-factory-4-special/80987735',
    warning: id === 'staff-damage' ? 'Strange Pendant ignores enemy DEF/M.DEF AND your own DEF/M.DEF. This damage-focused build sacrifices protection.' : 'Curated balanced staff build. Final resistances, accessory inheritance and charge attacks require in-game testing.' };
}

export function giveGearPreset(save, catalog, id, acknowledgeRisk = false) {
  save.requireSlot();
  if (acknowledgeRisk !== true) throw new Error('Acknowledge experimental gear presets first.');
  gearPreset(id, catalog); // Validate the complete set before any write.
  const preset = presetFor(id);
  // Restrict allocation to the first 15 slots, usable even without bag expansion.
  // Never unlock capacity or place rewards in potentially inaccessible slots.
  const slots = save.inventoryItems('bag').filter(item => item.slot < 15 && item.id === 0 && item.quantity === 0).slice(0, preset.items.length);
  if (slots.length !== preset.items.length) throw new Error('Free six slots in the first 15 bag slots before giving gear. Existing items are never overwritten.');
  return save.transact(preset.name, bytes => {
    const staged = Object.create(save);
    staged.data = bytes;
    staged.transact = (_label, edit) => { edit(bytes); return true; };
    preset.items.forEach((item, index) => {
      const details = { totalLevel: 150, rarityBonus: 200,
        ...Object.fromEntries(item.craft.map((id, i) => [`craft${i}`, id])),
        ...Object.fromEntries(item.upgrades.map((id, i) => [`upgrade${i}`, id])) };
      // Clear stale bytes in nominally empty records as a real item initializer does.
      const offset = slots[index].offset;
      bytes.fill(0, offset, offset + 28);
      editInventoryItem(staged, 'bag', slots[index].slot, { id: item.id, quantity: 1, level: 10 }, catalog.bagDefinition(item.id), catalog, details);
      // CT item-record +2 is the crafted/homemade marker. These are crafted sets,
      // not shop-bought level-10 equipment with uninitialized attachment data.
      bytes[offset + 2] = 1;
    });
  });
}
