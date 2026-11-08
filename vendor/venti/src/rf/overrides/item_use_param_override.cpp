#include "item_use_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../item_use_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_item_use_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<ItemUseParam>& config) {
    apply_all_overrides<ItemUseParam>(config, apply_item_use_param_overrides, mods, "use");
}

void apply_item_use_param_overrides(const toml::table& node, ItemUseParam& record) {
    read_override(node, "hp", record.hp);
    read_override(node, "rp", record.rp);
    read_override(node, "hp_pct", record.hp_pct);
    read_override(node, "rp_pct", record.rp_pct);
    read_override(node, "status_flags", record.status_flags);
    read_override(node, "effect_duration", record.effect_duration);
    read_override(node, "max_hp", record.max_hp);
    read_override(node, "max_rp", record.max_rp);
    read_override(node, "strength", record.strength);
    read_override(node, "intelligence", record.intelligence);
    read_override(node, "vitality", record.vitality);
    read_override(node, "max_hp_pct", record.max_hp_pct);
    read_override(node, "max_rp_pct", record.max_rp_pct);
    read_override(node, "strength_pct", record.strength_pct);
    read_override(node, "intelligence_pct", record.intelligence_pct);
    read_override(node, "vitality_pct", record.vitality_pct);
    read_override(node, "crit", record.crit);
    read_override(node, "knock_res", record.knock_res);
    read_override(node, "crit_res", record.crit_res);
    read_override(node, "poison_res", record.poison_res);
    read_override(node, "seal_res", record.seal_res);
    read_override(node, "paralysis_res", record.paralysis_res);
    read_override(node, "sleep_res", record.sleep_res);
    read_override(node, "fatigue_res", record.fatigue_res);
    read_override(node, "sick_res", record.sick_res);
    read_override(node, "faint_res", record.faint_res);
    read_override(node, "poison_atk", record.poison_atk);
    read_override(node, "seal_atk", record.seal_atk);
    read_override(node, "paralysis_atk", record.paralysis_atk);
    read_override(node, "sleep_atk", record.sleep_atk);
    read_override(node, "fatigue_atk", record.fatigue_atk);
    read_override(node, "sick_atk", record.sick_atk);
    read_override(node, "faint_atk", record.faint_atk);
    read_override(node, "fire_res", record.fire_res);
    read_override(node, "water_res", record.water_res);
    read_override(node, "earth_res", record.earth_res);
    read_override(node, "wind_res", record.wind_res);
    read_override(node, "light_res", record.light_res);
    read_override(node, "dark_res", record.dark_res);
    read_override(node, "love_res", record.love_res);
    read_override(node, "perm_hp", record.perm_hp);
    read_override(node, "perm_strength", record.perm_strength);
    read_override(node, "perm_intelligence", record.perm_intelligence);
    read_override(node, "perm_vitality", record.perm_vitality);
    read_override(node, "level_scaling", record.level_scaling);
}
} // namespace RFConfig
