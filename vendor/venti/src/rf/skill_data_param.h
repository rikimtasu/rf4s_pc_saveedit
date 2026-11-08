#pragma once

#include <cstdint>

namespace RFConfig {

// Skill experience and RP cost per action.
//
// Skill IDs, in order from 0: Short Sword, Long Sword, Spear, Axe/Hammer, Dual Blades, Fist, Fire, Water, Earth, Wind,
// Light, Dark, Love, Farming, Logging, Mining, Fishing, Cooking, Forging, Chemistry, Crafting, Searching, Walking,
// Sleeping, Eating, Defense, Resist Poison, Resist Seals, Resist Paralysis, Resist Sleep, Resist Fatigue, Resist Cold,
// Resist Knockout, Bathing, Taming, Throwing, Leadership, Bartering.
//
// File: rf3ParamSkillData.bin
struct SkillDataParam {
    // RP required to use the skill, as a percent of player's max RP, where 256 = 100%.
    uint32_t rp_cost_pct;

    // Flat RP cost required to use the skill. Acts as a minimum; if the record also defines `rp_cost_pct`, then the
    // actual RP used will be the greater of the two values.
    uint32_t rp_cost;

    // Skill-specific XP gained for `skill_1` per each use of this action.
    uint32_t skill_xp_1;

    // ID of the first skill increased by performing this action.
    uint32_t skill_1;

    // Skill-specific XP gained for `skill_2` per each use of this action.
    uint32_t skill_xp_2;

    // ID of the second skill increased by performing this action.
    uint32_t skill_2;

    // Skill-specific XP gained for `skill_3` per each use of this action.
    uint32_t skill_xp_3;

    // ID of the third skill increased by performing this action.
    uint32_t skill_3;
};

static_assert(sizeof(SkillDataParam) == 0x20);
} // namespace RFConfig
