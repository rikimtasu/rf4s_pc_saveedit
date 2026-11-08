#pragma once

#include "../config_data.h"
#include "../skill_stat.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `SkillStat` overrides in all loaded mods and applies all changes found.
void apply_all_skill_stat_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<SkillStat>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_skill_stat_overrides(const toml::table& node, SkillStat& record);
} // namespace RFConfig
