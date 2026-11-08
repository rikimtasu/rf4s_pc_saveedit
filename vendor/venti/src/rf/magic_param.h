#pragma once

#include <cstdint>

namespace RFConfig {

// Parameters for magic and abilities such as damage, status effects, and skill affinity.
//
// Percentage fields are fixed-point, where 4096 = 100%.
//
// File: rf3ParamMagic.bin
struct MagicParam {
    uint32_t unknown_0;            // 0x00
    uint32_t unknown_4;            // 0x04
    uint32_t unknown_8;            // 0x08
    uint32_t unknown_c;            // 0x0C
    uint32_t unknown_10;           // 0x10
    uint32_t unknown_14;           // 0x14
    uint32_t unknown_18;           // 0x18
    uint8_t damage_type_attribute; // 0x1C 0x80 = Magical, plus attribute bits: 0x01 = Fire, 0x02 = Water,
                                   //      0x04 = Earth, 0x08 = Wind, 0x10 = Light, 0x20 = Dark, 0x40 = Love
    uint8_t unknown_1d;            // 0x1D
    uint8_t unknown_1e;            // 0x1E
    uint8_t persists;              // 0x1F
    int32_t base_damage;           // 0x20
    uint32_t attack_scaling;       // 0x24 %
    uint32_t magic_attack_scaling; // 0x28 %
    uint32_t damage_scaling;       // 0x2C %
    uint32_t unknown_30;           // 0x30 %
    uint32_t unknown_34;           // 0x34 %
    uint32_t knock;                // 0x38 %
    uint32_t launch;               // 0x3C %
    uint32_t unknown_40;           // 0x40 %
    uint32_t unknown_44;           // 0x44 %
    uint32_t unknown_48;           // 0x48
    uint32_t unknown_4c;           // 0x4C
    uint32_t unknown_50;           // 0x50
    uint32_t unknown_54;           // 0x54
    uint32_t unknown_58;           // 0x58
    uint32_t hit_counter;          // 0x5C
    uint32_t dizzy;                // 0x60
    uint32_t poison_atk;           // 0x64 %
    uint32_t seal_atk;             // 0x68 %
    uint32_t paralysis_atk;        // 0x6C %
    uint32_t sleep_atk;            // 0x70 %
    uint32_t fatigue_atk;          // 0x74 %
    uint32_t sick_atk;             // 0x78 %
    uint32_t faint_atk;            // 0x7C %
    uint32_t drain_atk;            // 0x80 %
    uint32_t skill_exp;            // 0x84
    uint32_t rp_cost;              // 0x88
    uint32_t rp_cost_pct;          // 0x8C %
    uint32_t skill_type;           // 0x90 Fire, Water, Earth, Wind, Light, Dark, Love, Resist Poison, ...
};

static_assert(sizeof(MagicParam) == 0x94);
} // namespace RFConfig
