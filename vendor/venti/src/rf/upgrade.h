#pragma once

#include "item_status.h"

#include <cstdint>

namespace RFConfig {

// Stat bonuses granted by an item when used as an upgrade or cooking ingredient.
//
// Percentage fields are fixed-point, where 4096 = 100%.
//
// File: rf3ItemStrengthening.bin
struct Upgrade {
    uint32_t difficulty;           // Item's difficulty rating; higher difficulty requires more RP to upgrade.
    int32_t attack;                // Flat bonus to ATK.
    int32_t magic_attack;          // Flat bonus to M.ATK.
    int32_t defense;               // Flat bonus to DEF.
    int32_t magic_defense;         // Flat bonus to M.DEF.
    int32_t strength;              // Flat bonus to STR.
    int32_t intelligence;          // Flat bonus to INT.
    int32_t vitality;              // Flat bonus to VIT.
    int32_t dizzy;                 // Adds to weapon's dizzy rating; causes knockouts faster.
    uint32_t unknown_24;           // Unused by game.
    int32_t crit;                  // Bonus to critical hit rate (additive %).
    int32_t knock;                 // Bonus to knockback distance (additive %).
    int32_t stun;                  // Bonus to stun duration (additive %).
    uint32_t unknown_34;           // Unused by game.
    int32_t poison_atk;            // Bonus to poison infliction chance (%).
    int32_t seal_atk;              // Bonus to seal infliction chance (%).
    int32_t paralysis_atk;         // Bonus to paralysis infliction chance (%).
    int32_t sleep_atk;             // Bonus to sleep infliction chance (%).
    int32_t fatigue_atk;           // Bonus to fatigue infliction chance (%).
    int32_t sick_atk;              // Bonus to sick infliction chance (%).
    int32_t faint_atk;             // Bonus to faint (instant death) chance (%).
    int32_t drain_atk;             // Recovers % of damage dealt as HP; additive with multiple upgrades.
    int32_t dizzy_res;             // Reduction in received diz (slower knockout buildup) (%).
    int32_t crit_res;              // Reduction in received critical hit chance (%).
    int32_t knock_res;             // Reduction in knockback distance (%).
    int32_t poison_res;            // Additional chance to resist poison status (%).
    int32_t seal_res;              // Additional chance to resist seal status (%).
    int32_t paralysis_res;         // Additional chance to resist paralysis status (%).
    int32_t sleep_res;             // Additional chance to resist sleep status (%).
    int32_t fatigue_res;           // Additional chance to resist fatigue status (%).
    int32_t sick_res;              // Additional chance to resist sick status (%).
    int32_t faint_res;             // Additional chance to ignore an instant death proc (%).
    int32_t drain_res;             // Reduction in enemy HP absorption (%, additive).
    uint32_t hit_range;            // When applied to weapons, increases their attack range (%, additive).
    int32_t hp_cook;               // Additional HP recovered (flat) by cooked items using this as extra ingredient.
    int32_t rp_cook;               // Additional RP recovered (flat) by cooked items using this as extra ingredient.
    int32_t hp_cook_pct;           // Additional HP recovered (% of max) by cooked items using this as extra ingredient.
    int32_t rp_cook_pct;           // Additional RP recovered (% of max) by cooked items using this as extra ingredient.
    ItemStatusFlags status_cook;   // Additional status modifiers for cooked items using this as extra ingredient.
    uint32_t unknown_9c;           // Unused by game.
    int32_t max_hp_cook;           // Bonus to Max HP (flat) as a cooking ingredient.
    int32_t max_rp_cook;           // Bonus to Max RP (flat) as a cooking ingredient.
    int32_t strength_cook;         // Bonus to STR (flat) as a cooking ingredient.
    int32_t intelligence_cook;     // Bonus to INT (flat) as a cooking ingredient.
    int32_t vitality_cook;         // Bonus to VIT (flat) as a cooking ingredient.
    int32_t max_hp_cook_pct;       // Bonus to Max HP (% of normal) as a cooking ingredient.
    int32_t max_rp_cook_pct;       // Bonus to Max RP (% of normal) as a cooking ingredient.
    int32_t strength_cook_pct;     // Bonus to STR (%) as a cooking ingredient.
    int32_t intelligence_cook_pct; // Bonus to INT (%) as a cooking ingredient.
    int32_t vitality_cook_pct;     // Bonus to VIT (%) as a cooking ingredient.
    int32_t crit_cook;             // Bonus to critical chance (%) as a cooking ingredient.
    int32_t knock_res_cook;        // Bonus to knockback reduction (%) as a cooking ingredient.
    int32_t crit_res_cook;         // Bonus to critical resistance (%) as a cooking ingredient.
    int32_t poison_res_cook;       // Bonus to poison resistance (%) as a cooking ingredient.
    int32_t seal_res_cook;         // Bonus to seal resistance (%) as a cooking ingredient.
    int32_t paralysis_res_cook;    // Bonus to paralysis resistance (%) as a cooking ingredient.
    int32_t sleep_res_cook;        // Bonus to sleep resistance (%) as a cooking ingredient.
    int32_t fatigue_res_cook;      // Bonus to fatigue resistance (%) as a cooking ingredient.
    int32_t sick_res_cook;         // Bonus to sick resistance (%) as a cooking ingredient.
    int32_t faint_res_cook;        // Bonus to faint resistance (%) as a cooking ingredient.
    int32_t poison_atk_cook;       // Bonus to poison infliction chance (%) as a cooking ingredient.
    int32_t seal_atk_cook;         // Bonus to seal infliction chance (%) as a cooking ingredient (may not work).
    int32_t paralysis_atk_cook;    // Bonus to paralysis infliction chance (%) as a cooking ingredient (may not work).
    int32_t sleep_atk_cook;        // Bonus to sleep infliction chance (%) as a cooking ingredient (may not work).
    int32_t fatigue_atk_cook;      // Bonus to fatigue infliction chance (%) as a cooking ingredient (may not work).
    int32_t sick_atk_cook;         // Bonus to sick infliction chance (%) as a cooking ingredient (may not work).
    int32_t faint_atk_cook;        // Bonus to faint infliction chance (%) as a cooking ingredient (may not work).
    int32_t fire_res;              // Bonus to fire element resistance (%).
    int32_t water_res;             // Bonus to water element resistance (%).
    int32_t earth_res;             // Bonus to earth element resistance (%).
    int32_t wind_res;              // Bonus to wind element resistance (%).
    int32_t light_res;             // Bonus to light element resistance (%).
    int32_t dark_res;              // Bonus to dark element resistance (%).
    int32_t love_res;              // Bonus to love element resistance (%).
};

static_assert(sizeof(Upgrade) == 0x128);
} // namespace RFConfig
