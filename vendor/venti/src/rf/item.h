#pragma once

#include <cstdint>

namespace RFConfig {

// Item categories used in the game.
enum class ItemCategory : uint8_t {
    Vegetable = 0,
    Fruit = 1,
    Plant = 2,
    Medicine = 3,
    Fail = 4,             // Failed dish, disastrous dish
    Knife = 5,            // Cooked dish, using knife
    FryingPan = 6,        // Cooked dish, using frying pan
    Pot = 7,              // Cooked dish, using pot
    Oven = 8,             // Cooked dish, using oven
    Mixer = 9,            // Cooked dish, using mixer
    Steamed = 10,         // Cooked dish, using steamer
    Handmade = 11,        // Simple cooking, in-game description is "No Tool"
    ReadyMade = 12,       // Bought ingredients like Rice and Chocolate
    Dairy = 13,           // All animal products including Milk, Eggs, Honey, etc.
    Ingredient = 14,      // "Basic" ingredients: flour, oil, etc.
    ShortSword = 15,
    LongSword = 16,
    Spear = 17,
    Hammer = 18,
    Axe = 19,
    Staff = 24,
    DualBlades = 25,
    Fist = 26,
    Hoe = 27,
    Waterpot = 28,
    Sickle = 29,
    MiningHammer = 30,    // Farm tool version, in-game description is "Hammer"
    ChoppingAxe = 31,     // Farm tool version, in-game description is "Axe"
    Pole = 32,            // Fishing rod
    Shield = 33,
    Accessory = 34,
    Headgear = 35,
    Shoes = 36,
    Armor = 37,
    Brush = 40,           // Only used for the Brush item
    Clippers = 41,        // Only used for the Clippers item
    MagnifyingGlass = 45, // Only used for the Magnifying Glass item
    Seed = 46,
    Nutrient = 47,        // Formula A/B/C, Greenifiers, etc.
    Magic = 48,
    RuneAbility = 49,
    Special = 50,         // Unique/song abilities e.g. Bonus Concerto
    Collectible = 51,     // Monster/geode drops, plus Fodder
    Fish = 52,
    Trash = 53,
    Other = 54,           // Rock, Branch, Lumber, Material Stone
    Category = 55,        // Literally a subcategory like "Strings" or "Shards"
    RecipeBread = 57,
};

// Item properties and stat bonuses, stored in `Item::flags`.
enum class ItemFlags : uint32_t {
    None = 0,
    NonDiscardable = 0x0001,
    KeyItem = 0x0002,
    SpecialCatch = 0x0004,      // Special fishing catch
    Giant = 0x0008,             // Giant crop
    AttackBonus = 0x0010,
    DefenseBonus = 0x0020,
    MagicAttackBonus = 0x0040,
    MagicDefenseBonus = 0x0080,
    Unknown100 = 0x0100,        // Only used by Magic Shield (item 603)
};

constexpr ItemFlags operator|(ItemFlags a, ItemFlags b) {
    return static_cast<ItemFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr ItemFlags operator&(ItemFlags a, ItemFlags b) {
    return static_cast<ItemFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr ItemFlags operator~(ItemFlags a) {
    return static_cast<ItemFlags>(~static_cast<uint32_t>(a));
}

constexpr ItemFlags& operator|=(ItemFlags& a, ItemFlags b) {
    return a = a | b;
}

constexpr ItemFlags& operator&=(ItemFlags& a, ItemFlags b) {
    return a = a & b;
}

// General item properties such as type, rarity and price.
//
// File: rf3ItemList.bin
struct Item {
    // ID of a family of related items. Mainly used for recipe slots.
    uint32_t family;

    // ID of the category that is displayed in the game UI such as "Vegetable" or "Ready-Made".
    ItemCategory category;

    // Single byte holding both the rarity (high 4 bits) and max stack size (low 4 bits). Use the `rarity` and
    // `max_stack` accessors to read or write each part separately.
    uint8_t rarity_max_stack;

    // Index of the `PriceTable` record that holds the buying price multiplier at each item level.
    uint8_t buy_rate_index;

    // Index of the `PriceTable` record that holds the selling price multiplier at each item level.
    uint8_t sell_rate_index;

    // Base price to buy the level 1 item at a shop. Modified by `buy_rate_index` at higher levels.
    uint32_t buy;

    // Base price to sell or ship the level 1 item. Modified by `sell_rate_index` at higher levels.
    uint32_t sell;

    // Index into `Crop`, either grown by a seed or used to grow a product.
    uint32_t crop;

    // Miscellaneous flags attached to the item, affecting different parts of the game's behavior.
    ItemFlags flags;

    // Apparently unused field, populated and unique per type, but never read by the game.
    int32_t unknown_18;

    // Story progress required for automatic unlock of this item in shops.
    //
    // "Automatic" in this context means that the item is always guaranteed to unlock at this point, but may have been
    // unlocked earlier by an event or by picking up the item as loot.
    uint32_t story_unlock;

    // Order within the item's category in game menus
    uint32_t sort_order;

    // For staves, the level of the charged shot. Some other items have nonzero values but they appear to be unused.
    uint16_t staff_shot_level;

    // Apparently unused.
    uint16_t unknown_26;

    // Rarity, from 0 to 15; stored in the high 4 bits of `rarity_max_stack`.
    [[nodiscard]] uint8_t rarity() const {
        return rarity_max_stack >> 4;
    }

    // Max stack size, from 0 to 15; stored in the low 4 bits of `rarity_max_stack`.
    [[nodiscard]] uint8_t max_stack() const {
        return rarity_max_stack & 0x0F;
    }

    // Sets the rarity, keeping the max stack size. Only the low 4 bits of `value` are used.
    void set_rarity(uint8_t value) {
        rarity_max_stack = static_cast<uint8_t>((rarity_max_stack & 0x0F) | ((value & 0x0F) << 4));
    }

    // Sets the max stack size, keeping the rarity. Only the low 4 bits of `value` are used.
    void set_max_stack(uint8_t value) {
        rarity_max_stack = static_cast<uint8_t>((rarity_max_stack & 0xF0) | (value & 0x0F));
    }
};

static_assert(sizeof(Item) == 0x28);
} // namespace RFConfig
