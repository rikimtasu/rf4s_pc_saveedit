#pragma once

#include <cstdint>

namespace RFConfig {

// Stat gains per skill level.
//
// Records are indexed by skill ID (see `SkillDataParam`), followed by two unused records.
//
// All fields are fixed-point percentages, where 4096 = 100%.
//
// File: rf3ParamSkill.bin
struct SkillStat {
    uint32_t hp;           // Gain to max HP.
    uint32_t rp;           // Gain to max RP.
    uint32_t strength;     // Gain to STR attribute.
    uint32_t intelligence; // Gain to INT attribute.
    uint32_t vitality;     // Gain to VIT attribute.
    uint32_t attack;       // Gain to weapon ATK, but has unintuitive behavior in game.
    uint32_t unknown_18;   // Unused, never read by game.
    uint32_t magic_attack; // Gain to M.ATK, only applies to magic skills.
    uint32_t resistance;   // Elemental resistance gained/damage reduced; for magic skills only.
    uint32_t rp_reduction; // Reduction in RP cost.
};

static_assert(sizeof(SkillStat) == 0x28);
} // namespace RFConfig
