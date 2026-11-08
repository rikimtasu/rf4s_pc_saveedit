#include "magic_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../magic_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_magic_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<MagicParam>& config) {
    apply_all_overrides<MagicParam>(config, apply_magic_param_overrides, mods, "magic");
}

void apply_magic_param_overrides(const toml::table& node, MagicParam& record) {
    read_override(node, "damage_type_attribute", record.damage_type_attribute);
    read_override(node, "persists", record.persists);
    read_override(node, "base_damage", record.base_damage);
    read_override(node, "attack_scaling", record.attack_scaling);
    read_override(node, "magic_attack_scaling", record.magic_attack_scaling);
    read_override(node, "damage_scaling", record.damage_scaling);
    read_override(node, "knock", record.knock);
    read_override(node, "launch", record.launch);
    read_override(node, "hit_counter", record.hit_counter);
    read_override(node, "dizzy", record.dizzy);
    read_override(node, "poison_atk", record.poison_atk);
    read_override(node, "seal_atk", record.seal_atk);
    read_override(node, "paralysis_atk", record.paralysis_atk);
    read_override(node, "sleep_atk", record.sleep_atk);
    read_override(node, "fatigue_atk", record.fatigue_atk);
    read_override(node, "sick_atk", record.sick_atk);
    read_override(node, "faint_atk", record.faint_atk);
    read_override(node, "drain_atk", record.drain_atk);
    read_override(node, "skill_exp", record.skill_exp);
    read_override(node, "rp_cost", record.rp_cost);
    read_override(node, "rp_cost_pct", record.rp_cost_pct);
    read_override(node, "skill_type", record.skill_type);
}
} // namespace RFConfig
