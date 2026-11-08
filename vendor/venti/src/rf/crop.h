#pragma once

#include <cstdint>

namespace RFConfig {

// Crop properties and seasonal growth modifiers, stored in `Crop::flags`.
//
// Seasons with neither a good nor a poor flag are neutral. On wild plants such as Blue Grass and Bamboo Sprout, the
// "good" season flags appear to mark the season they spawn in.
enum class CropFlags : uint32_t {
    None = 0,
    MaybeForage = 0x00001,  // Wild item that can be picked up, e.g. Rock, Branch, wild grasses and herbs, Weeds
    Unknown2 = 0x00002,     // Only used by unnamed obstacles (records 2, 4, 5, 22, 24, 26-37)
    Unknown4 = 0x00004,     // Rocks, branches, obstacles, Weeds, Withered Grass, Fodder and others
    Plant = 0x00008,        // All plants, crops and trees
    Seeded = 0x00010,       // Grown from a seed
    Minable = 0x00020,      // Broken with a hammer
    Choppable = 0x00040,    // Broken with an axe
    Flower = 0x00080,       // Toyherb, Pink Cat, etc.
    Vegetable = 0x00100,    // Includes fruit such as Strawberry and Pineapple
    Tree = 0x00200,         // Fruit trees
    DungeonField = 0x00400, // Only used by Field Dungeon
    SpringGood = 0x01000,   // Faster growth in spring
    SummerGood = 0x02000,   // Faster growth in summer
    FallGood = 0x04000,     // Faster growth in fall
    WinterGood = 0x08000,   // Faster growth in winter
    SpringPoor = 0x10000,   // Slower growth in spring
    SummerPoor = 0x20000,   // Slower growth in summer
    FallPoor = 0x40000,     // Slower growth in fall
    WinterPoor = 0x80000,   // Slower growth in winter
};

constexpr CropFlags operator|(CropFlags a, CropFlags b) {
    return static_cast<CropFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr CropFlags operator&(CropFlags a, CropFlags b) {
    return static_cast<CropFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr CropFlags operator~(CropFlags a) {
    return static_cast<CropFlags>(~static_cast<uint32_t>(a));
}

constexpr CropFlags& operator|=(CropFlags& a, CropFlags b) {
    return a = a | b;
}

constexpr CropFlags& operator&=(CropFlags& a, CropFlags b) {
    return a = a & b;
}

// Growth parameters for crops.
//
// Soil XP fields and the growth and harvest rates/costs (0x40 to 0x5C) are fixed-point, where 32 = 1.0.
//
// File: rf3CropParam.bin
struct Crop {
    // Number of in-game days required for the first growth stage.
    uint8_t stage_1_days;

    // Number of in-game days required for the second growth stage.
    uint8_t stage_2_days;

    // Number of in-game days required for the third growth stage.
    uint8_t stage_3_days;

    // Number of in-game days required for the fourth and final growth stage.
    uint8_t stage_4_days;

    // Sprite size during the first growth stage. Usually 0, negative values make the sprite smaller.
    // Unconfirmed in game.
    int8_t stage_1_size;

    // Sprite size during the second growth stage.
    // Unconfirmed in game.
    int8_t stage_2_size;

    // Sprite size during the third growth stage.
    // Unconfirmed in game.
    int8_t stage_3_size;

    // Sprite size during the fourth and final growth stage.
    // Unconfirmed in game.
    int8_t stage_4_size;

    // Sprite size of the giant variant.
    // Unconfirmed in game.
    int16_t giant_sprite_size;

    // Sprite size when withered.
    // Unconfirmed in game.
    int16_t withered_sprite_size;

    // Chance of spawning in the wild. Only the low 16 bits are used.
    // Unconfirmed in game.
    uint32_t wild_spawn_chance;

    // Initial HP.
    uint32_t initial_hp;

    // Size used for collisions, where 16 = 100%.
    uint32_t collision_size;

    // Number of in-game days required to regrow after harvesting, or 0 if the crop does not regrow.
    uint32_t regrowth_days;

    // Number of items yielded per harvest.
    uint32_t yield;

    // Defense (for typhoons), up to 63.
    uint32_t defense;

    // Chance of triggering an NPC visit/event when harvesting.
    // Unconfirmed in game.
    uint32_t harvest_event_chance;

    // Soil health lost when harvesting. Only the low 16 bits are used.
    uint32_t harvest_health_cost;

    // Soil XP gained for the overall level.
    uint32_t soil_xp_overall;

    // Soil XP gained for growth speed.
    uint32_t soil_xp_speed;

    // Soil XP gained for quality.
    uint32_t soil_xp_quality;

    // Soil XP gained for size.
    uint32_t soil_xp_size;

    // Soil XP gained for yield.
    uint32_t soil_xp_yield;

    // Rate of progression through the different growth stages, per in-game day.
    uint32_t growth_rate;

    // Rate at which quality (harvested crop level) increases, per in-game day.
    uint32_t quality_gain_rate;

    // Rate at which size (progress toward giant-ness) increases, per in-game day.
    uint32_t size_gain_rate;

    // Rate at which `yield` increases, per in-game day.
    uint32_t yield_gain_rate;

    // Amount subtracted from the soil's growth rate when this crop is harvested.
    uint32_t harvest_growth_cost;

    // Amount subtracted from the soil's quality when this crop is harvested.
    uint32_t harvest_quality_cost;

    // Amount subtracted from the soil's size (giant-ness of crops grown on that soil) when this crop is harvested.
    uint32_t harvest_size_cost;

    // Amount subtracted from the soil's yield when this crop is harvested.
    uint32_t harvest_yield_cost;

    // Item ID of the main product received when harvesting.
    uint32_t harvest_item;

    // Item ID of the additional seed that may be dropped when harvesting.
    uint32_t seed_item;

    // Good and poor growing seasons, along with other crop properties.
    CropFlags flags;
};

static_assert(sizeof(Crop) == 0x6C);
} // namespace RFConfig
