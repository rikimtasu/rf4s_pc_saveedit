#pragma once

#include <cstdint>

namespace RFConfig {

// Rates for spawning a single type of fish, per map location.
//
// Appear to be weightings, rather than absolute values. For example, there are only two fish in the Sand Pond,
// Sand Flounder at 1150 and Rockfish at 59, which means Sand Flounder is about 20 times more likely to spawn.
// Other areas have different weights for different fish, some as low as 2 or as high as 1500. They don't add up to
// anything in particular and there is no "nothing" or "default" catch option, therefore, the values are relatively only
// to other values in the same area.
//
// Seasonal fields (`spring`, `summer`, etc.) refer to fish spawned in the village during that season, and also to any
// rivers/ponds outside the village that are permanently in that season; the `_rain` and `_snow` fields are the same
// thing, but when the weather is rainy (or snowing, in winter).
//
// Other fields refer to specific map areas or special rerolls.
//
// Files: Fishing_rate_fish_Spring.bin, Fishing_rate_fish_Spring2.bin
struct FishRate {
    // Spawn weight in spring, clear weather.
    uint32_t spring;

    // Spawn weight in spring, rainy weather; also in Idra Cave, 1F.
    uint32_t spring_rain;

    // Spawn weight in summer, clear weather.
    uint32_t summer;

    // Spawn weight in summer, rainy weather.
    uint32_t summer_rain;

    // Spawn weight in fall, clear weather.
    uint32_t fall;

    // Spawn weight in fall, rainy weather.
    uint32_t fall_rain;

    // Spawn weight in winter, clear weather.
    uint32_t winter;

    // Spawn weight in winter, when snowing.
    uint32_t winter_snow;

    // Spawn weight in the Sand Pond.
    uint32_t sand;

    // Spawn weight in Idra Cave, B2.
    uint32_t idra_b2;

    // Spawn weight in Idra Cave, B1.
    uint32_t idra_b1;

    // Spawn weight in Yokmir Forest, waterfall area.
    uint32_t yokmir_waterfall;

    // Spawn weight in Yokmir Forest, pond area.
    uint32_t yokmir_pond;

    // Spawn weight in the Water Ruins.
    uint32_t water_ruins;

    // Spawn weight in Maya Road.
    uint32_t maya_road;

    // Spawn weight in the Sechs Cave.
    uint32_t sechs_cave;

    // Catch weight when rerolling a trash item caught with the tier 0 pole (Cheap Pole).
    uint32_t trash_0;

    // Catch weight when rerolling a trash item caught with the tier 1 pole (Beginner's Pole).
    uint32_t trash_1;

    // Catch weight when rerolling a trash item caught with the tier 2 pole (Skilled Pole).
    uint32_t trash_2;

    // Catch weight when rerolling a trash item caught with the tier 3 pole (Famous Pole).
    uint32_t trash_3;

    // Catch weight when rerolling a trash item caught with the tier 4 pole (Sacred Pole).
    uint32_t trash_4;

    // Column index or "category" to look up in `FishLevelRate` when determining the size/level.
    uint32_t level_rate_index;
};

static_assert(sizeof(FishRate) == 0x58);
} // namespace RFConfig
