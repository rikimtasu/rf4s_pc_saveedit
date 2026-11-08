#pragma once

#include "../config_data.h"
#include "../geode_rate.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `GeodeRate` overrides in all loaded mods and applies all changes found.
void apply_all_geode_rate_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<GeodeRate>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_geode_rate_overrides(const toml::table& node, GeodeRate& record);
} // namespace RFConfig
