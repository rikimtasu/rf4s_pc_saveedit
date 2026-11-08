#pragma once

#include "../config_data.h"
#include "../crop.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `Crop` overrides in all loaded mods and applies all changes found.
void apply_all_crop_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Crop>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_crop_overrides(const toml::table& node, Crop& record);
} // namespace RFConfig
