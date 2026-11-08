#include "skill_data_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../skill_data_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_skill_data_param_overrides(const std::vector<Mods::LoadedMod>& mods,
                                          ConfigFile<SkillDataParam>& config) {
    apply_all_overrides<SkillDataParam>(config, apply_skill_data_param_overrides, mods, "skill_action");
}

void apply_skill_data_param_overrides(const toml::table& node, SkillDataParam& record) {
    read_override(node, "rp_cost_pct", record.rp_cost_pct);
    read_override(node, "rp_cost", record.rp_cost);
    read_override(node, "skill_xp_1", record.skill_xp_1);
    read_override(node, "skill_1", record.skill_1);
    read_override(node, "skill_xp_2", record.skill_xp_2);
    read_override(node, "skill_2", record.skill_2);
    read_override(node, "skill_xp_3", record.skill_xp_3);
    read_override(node, "skill_3", record.skill_3);
}
} // namespace RFConfig
