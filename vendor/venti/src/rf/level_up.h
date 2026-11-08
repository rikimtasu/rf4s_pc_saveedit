#pragma once

#include <cstdint>

namespace RFConfig {

// Player experience required and target stats per level.
//
// Target stats mean the stats the player would have assuming no modifiers have been applied, including permanent
// modifiers such as gains from medicine (e.g. The Protein). Upon level up, the game takes the difference between the
// target stat at next level and the target stat at current level, and adds that difference to the player's current
// stat, so non-level-related stat gains are never lost unless absolute stat caps are exceeded.
//
// File: rf3Parameter.bin
struct LevelUp {
    uint32_t xp;           // XP required to reach this level from the previous level.
    uint32_t hp;           // Max HP at this level.
    uint32_t rp;           // Max RP at this level.
    uint32_t strength;     // STR stat at this level.
    uint32_t intelligence; // INT stat at this level.
    uint32_t vitality;     // VIT stat at this level.
};

static_assert(sizeof(LevelUp) == 0x18);
} // namespace RFConfig
