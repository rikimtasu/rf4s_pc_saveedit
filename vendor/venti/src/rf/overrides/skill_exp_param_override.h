#pragma once

#include "../config_data.h"
#include "../skill_exp_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `SkillExpParam` overrides in all loaded mods and applies all changes found.
//
// `partition_name` is the skill category:
// - `combat`: main `rf3ParamSkillExp` used for primarily combat skills
// - `tools`, in `rf3ParamSkillExpParam`, covering farm skills, logging, mining, etc.
// - `field`, in `rf3ParamSkillExpFish`, including field activities such as fishing, leadership, resistances, etc.
// - `synthesis`, in `rf3ParamSkillExpMix`, used for all crafting (equipment, weapons, cooking variants)
// - `lifestyle`, in `rf3ParamSkillExpSleep`, mainly sleeping, eating and bathing.
void apply_all_skill_exp_param_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                         ConfigFile<SkillExpParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_skill_exp_param_overrides(const toml::table& node, SkillExpParam& record);
} // namespace RFConfig
