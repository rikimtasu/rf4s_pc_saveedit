#pragma once

#include "../config_data.h"
#include "../upgrade.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `Upgrade` overrides in all loaded mods and applies all changes found.
void apply_all_upgrade_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Upgrade>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_upgrade_overrides(const toml::table& node, Upgrade& record);
} // namespace RFConfig
