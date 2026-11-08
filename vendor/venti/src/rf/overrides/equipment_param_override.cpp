#include "equipment_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../equipment_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_equipment_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<EquipmentParam>& config) {
    apply_all_overrides<EquipmentParam>(config, apply_equipment_param_overrides, mods, "equipment");
}

void apply_equipment_param_overrides(const toml::table& node, EquipmentParam& record) {
    read_override(node, "gear_params", record.gear_params);
    read_override(node, "boot_params", record.boot_params);
    read_override(node, "acc_params", record.acc_params);
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
    read_override(node, "fire_res", record.fire_res);
    read_override(node, "water_res", record.water_res);
    read_override(node, "earth_res", record.earth_res);
    read_override(node, "wind_res", record.wind_res);
    read_override(node, "light_res", record.light_res);
    read_override(node, "dark_res", record.dark_res);
    read_override(node, "love_res", record.love_res);
    read_override(node, "physical_res", record.physical_res);
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
    read_override(node, "depth", record.depth);
    read_override(node, "hit_range", record.hit_range);
    read_override(node, "hit_arc", record.hit_arc);
    read_override(node, "model", record.model);
}
} // namespace RFConfig
