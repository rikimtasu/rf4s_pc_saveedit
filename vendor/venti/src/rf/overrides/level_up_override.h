#pragma once

#include "../config_data.h"
#include "../level_up.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `LevelUp` overrides in all loaded mods and applies all changes found.
void apply_all_level_up_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<LevelUp>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_level_up_overrides(const toml::table& tbl, LevelUp& record);
} // namespace RFConfig
