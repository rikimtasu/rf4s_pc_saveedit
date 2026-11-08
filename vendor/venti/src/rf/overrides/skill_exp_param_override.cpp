#include "skill_exp_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../skill_exp_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_skill_exp_param_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                         ConfigFile<SkillExpParam>& config) {
    apply_all_overrides<SkillExpParam>(config, apply_skill_exp_param_overrides, mods, "skill_exp", partition_name);
}

void apply_skill_exp_param_overrides(const toml::table& node, SkillExpParam& record) {
    read_override(node, "xp", record.xp);
}
} // namespace RFConfig
