#pragma once

#include "item_status.h"

#include <cstdint>

namespace RFConfig {

// Effects of using (eating/drinking) an item, one record per item.
//
// Percentage fields are fixed-point, where 4096 = 100%.
//
// File: rf3UseItemParam.bin
struct ItemUseParam {
    int32_t hp;                   // HP gained/lost on use, absolute.
    int32_t rp;                   // RP gained/lost on use, absolute.
    int32_t hp_pct;               // HP gained/lost on use, % of max.
    int32_t rp_pct;               // RP gained/lost on use, % of max.
    ItemStatusFlags status_flags; // Status effects caused or cured.
    uint32_t effect_duration;     // Duration of temporary effects, in units of 3 in-game minutes.
    int32_t max_hp;               // Max HP gained/lost on use, absolute.
    int32_t max_rp;               // Max RP gained/lost on use, absolute.
    int32_t strength;             // STR gained/lost on use, absolute.
    int32_t intelligence;         // INT gained/lost on use, absolute.
    int32_t vitality;             // VIT gained/lost on use, absolute.
    int32_t max_hp_pct;           // Max HP gained/lost on use, % of natural max.
    int32_t max_rp_pct;           // Max RP gained/lost on use, % of natural max.
    int32_t strength_pct;         // STR gained/lost on use, % of natural value.
    int32_t intelligence_pct;     // INT gained/lost on use, % of natural value.
    int32_t vitality_pct;         // VIT gained/lost on use, % of natural value.
    int32_t crit;                 // Critical hit rate boost/reduction, flat %.
    int32_t knock_res;            // Knock resistance boost/reduction, flat %.
    int32_t crit_res;             // Critical hit resistance boost/reduction, flat %.
    int32_t poison_res;           // Poison resistance boost/reduction, flat %.
    int32_t seal_res;             // Seal resistance boost/reduction, flat %.
    int32_t paralysis_res;        // Paralysis resistance boost/reduction, flat %.
    int32_t sleep_res;            // Sleep resistance boost/reduction, flat %.
    int32_t fatigue_res;          // Fatigue resistance boost/reduction, flat %.
    int32_t sick_res;             // Sick resistance boost/reduction, flat %.
    int32_t faint_res;            // Faint resistance boost/reduction, flat %.
    int32_t poison_atk;           // Additional/reduced chance to inflict poison on attack, flat %.
    int32_t seal_atk;             // Additional/reduced chance to inflict seal on attack, flat %.
    int32_t paralysis_atk;        // Additional/reduced chance to inflict paralysis on attack, flat %.
    int32_t sleep_atk;            // Additional/reduced chance to inflict sleep on attack, flat %.
    int32_t fatigue_atk;          // Additional/reduced chance to inflict fatigue on attack, flat %.
    int32_t sick_atk;             // Additional/reduced chance to inflict sick on attack, flat %.
    int32_t faint_atk;            // Additional/reduced chance to inflict faint on attack, flat %.
    int32_t fire_res;             // Fire element resistance boost/reduction, flat %.
    int32_t water_res;            // Water element resistance boost/reduction, flat %.
    int32_t earth_res;            // Earth element resistance boost/reduction, flat %.
    int32_t wind_res;             // Wind element resistance boost/reduction, flat %.
    int32_t light_res;            // Light element resistance boost/reduction, flat %.
    int32_t dark_res;             // Dark element resistance boost/reduction, flat %.
    int32_t love_res;             // Love element resistance boost/reduction, flat %.
    int32_t perm_hp;              // Permanent HP gained, absolute.
    int32_t perm_strength;        // Permanent STR gained, absolute.
    int32_t perm_intelligence;    // Permanent INT gained, absolute.
    int32_t perm_vitality;        // Permanent VIT gained, absolute.
    int32_t level_scaling;        // Per-level scaling of effects, where 4096 = 12.5%.
};

static_assert(sizeof(ItemUseParam) == 0xB4);
} // namespace RFConfig
