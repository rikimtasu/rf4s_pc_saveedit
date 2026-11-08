#pragma once

#include <cstdint>

namespace RFConfig {

// Skill experience required per level, with one record per level from 0 to 99.
//
// Each skill category has its own file, all sharing this layout:
// - Combat (rf3ParamSkillExp.bin): all weapon and magic skills, Walking, Bartering
// - Farm Tools (rf3ParamSkillExpFarm.bin): Farming, Mining, Logging
// - Field Activity (rf3ParamSkillExpFish.bin): Fishing, Searching, Taming, Throwing, Resistances, Leadership
// - Synthesis (rf3ParamSkillExpMix.bin): Forging, Crafting, Cooking, Chemistry
// - Lifestyle (rf3ParamSkillExpSleep.bin): Sleeping, Eating, Bathing
struct SkillExpParam {
    // XP required for this level.
    uint32_t xp;
};

static_assert(sizeof(SkillExpParam) == 0x04);
} // namespace RFConfig
