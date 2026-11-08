#include "upgrade_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../upgrade.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_upgrade_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Upgrade>& config) {
    apply_all_overrides<Upgrade>(config, apply_upgrade_overrides, mods, "upgrade");
}

void apply_upgrade_overrides(const toml::table& node, Upgrade& record) {
    read_override(node, "difficulty", record.difficulty);
    read_override(node, "attack", record.attack);
    read_override(node, "magic_attack", record.magic_attack);
    read_override(node, "defense", record.defense);
    read_override(node, "magic_defense", record.magic_defense);
    read_override(node, "strength", record.strength);
    read_override(node, "intelligence", record.intelligence);
    read_override(node, "vitality", record.vitality);
    read_override(node, "dizzy", record.dizzy);
    read_override(node, "crit", record.crit);
    read_override(node, "knock", record.knock);
    read_override(node, "stun", record.stun);
    read_override(node, "poison_atk", record.poison_atk);
    read_override(node, "seal_atk", record.seal_atk);
    read_override(node, "paralysis_atk", record.paralysis_atk);
    read_override(node, "sleep_atk", record.sleep_atk);
    read_override(node, "fatigue_atk", record.fatigue_atk);
    read_override(node, "sick_atk", record.sick_atk);
    read_override(node, "faint_atk", record.faint_atk);
    read_override(node, "drain_atk", record.drain_atk);
    read_override(node, "dizzy_res", record.dizzy_res);
    read_override(node, "crit_res", record.crit_res);
    read_override(node, "knock_res", record.knock_res);
    read_override(node, "poison_res", record.poison_res);
    read_override(node, "seal_res", record.seal_res);
    read_override(node, "paralysis_res", record.paralysis_res);
    read_override(node, "sleep_res", record.sleep_res);
    read_override(node, "fatigue_res", record.fatigue_res);
    read_override(node, "sick_res", record.sick_res);
    read_override(node, "faint_res", record.faint_res);
    read_override(node, "drain_res", record.drain_res);
    read_override(node, "hit_range", record.hit_range);
    read_override(node, "hp_cook", record.hp_cook);
    read_override(node, "rp_cook", record.rp_cook);
    read_override(node, "hp_cook_pct", record.hp_cook_pct);
    read_override(node, "rp_cook_pct", record.rp_cook_pct);
    read_override(node, "status_cook", record.status_cook);
    read_override(node, "max_hp_cook", record.max_hp_cook);
    read_override(node, "max_rp_cook", record.max_rp_cook);
    read_override(node, "strength_cook", record.strength_cook);
    read_override(node, "intelligence_cook", record.intelligence_cook);
    read_override(node, "vitality_cook", record.vitality_cook);
    read_override(node, "max_hp_cook_pct", record.max_hp_cook_pct);
    read_override(node, "max_rp_cook_pct", record.max_rp_cook_pct);
    read_override(node, "strength_cook_pct", record.strength_cook_pct);
    read_override(node, "intelligence_cook_pct", record.intelligence_cook_pct);
    read_override(node, "vitality_cook_pct", record.vitality_cook_pct);
    read_override(node, "crit_cook", record.crit_cook);
    read_override(node, "knock_res_cook", record.knock_res_cook);
    read_override(node, "crit_res_cook", record.crit_res_cook);
    read_override(node, "poison_res_cook", record.poison_res_cook);
    read_override(node, "seal_res_cook", record.seal_res_cook);
    read_override(node, "paralysis_res_cook", record.paralysis_res_cook);
    read_override(node, "sleep_res_cook", record.sleep_res_cook);
    read_override(node, "fatigue_res_cook", record.fatigue_res_cook);
    read_override(node, "sick_res_cook", record.sick_res_cook);
    read_override(node, "faint_res_cook", record.faint_res_cook);
    read_override(node, "poison_atk_cook", record.poison_atk_cook);
    read_override(node, "seal_atk_cook", record.seal_atk_cook);
    read_override(node, "paralysis_atk_cook", record.paralysis_atk_cook);
    read_override(node, "sleep_atk_cook", record.sleep_atk_cook);
    read_override(node, "fatigue_atk_cook", record.fatigue_atk_cook);
    read_override(node, "sick_atk_cook", record.sick_atk_cook);
    read_override(node, "faint_atk_cook", record.faint_atk_cook);
    read_override(node, "fire_res", record.fire_res);
    read_override(node, "water_res", record.water_res);
    read_override(node, "earth_res", record.earth_res);
    read_override(node, "wind_res", record.wind_res);
    read_override(node, "light_res", record.light_res);
    read_override(node, "dark_res", record.dark_res);
    read_override(node, "love_res", record.love_res);
}
} // namespace RFConfig
