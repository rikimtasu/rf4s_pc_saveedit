#pragma once

#include <cstdint>

namespace RFConfig {

// Drops from mining geodes.
//
// File: MapOre_Rate.bin
struct GeodeRate {
    // Identifies the kind of geode; controls which sprite is drawn and which name is displayed.
    uint32_t kind;

    // Percentage chance of the geode breaking with each mining hit, where 256 = 100%. Lower values mean that the geode
    // can be hit more times (and produce more ore) before disappearing.
    //
    // This is the baseline stat, not taking into account reductions from hammer tier, mining skill, etc.
    uint32_t break_chance;

    // Percentage chance of dropping scrap metal instead of _any_ of the configured drops, where 256 = 100%.
    //
    // This is the baseline stat, not taking into account reductions from hammer tier, mining skill, etc.
    uint32_t scrap_chance; // 0x08

    // Likelihood of mining `drop_item_1` on each hit, relative to the other drop weights.
    uint32_t drop_weight_1;

    // Likelihood of mining `drop_item_2` on each hit, relative to the other drop weights.
    uint32_t drop_weight_2;

    // Likelihood of mining `drop_item_3` on each hit, relative to the other drop weights.
    uint32_t drop_weight_3;

    // First item that can be mined.
    uint16_t drop_item_1;

    // Second item that can be mined.
    uint16_t drop_item_2;

    // Third item that can be mined.
    uint16_t drop_item_3;

    // An additional, very rare drop whose drop rate is hardcoded in the game and never rises above 10% at the max
    // possible level and with the best possible equipment.
    //
    // None of the `drop_weight` fields affect this drop, it is always rare and always takes priority over all other
    // drops when the game rolls it.
    uint16_t drop_item_rare;
};

static_assert(sizeof(GeodeRate) == 0x20);
} // namespace RFConfig
