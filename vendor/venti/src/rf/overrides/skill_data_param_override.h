#pragma once

#include "../config_data.h"
#include "../skill_data_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `SkillDataParam` overrides in all loaded mods and applies all changes found.
void apply_all_skill_data_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<SkillDataParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_skill_data_param_overrides(const toml::table& node, SkillDataParam& record);
} // namespace RFConfig
