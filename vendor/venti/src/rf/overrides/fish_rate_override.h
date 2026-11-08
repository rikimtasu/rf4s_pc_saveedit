#pragma once

#include "../config_data.h"
#include "../fish_rate.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `FishRate` overrides in all loaded mods and applies all changes found.
//
// `partition_name` is the file variant: `spring` (Fishing_rate_fish_Spring.bin) or `spring2`
// (Fishing_rate_fish_Spring2.bin).
void apply_all_fish_rate_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                   ConfigFile<FishRate>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_fish_rate_overrides(const toml::table& node, FishRate& record);
} // namespace RFConfig
