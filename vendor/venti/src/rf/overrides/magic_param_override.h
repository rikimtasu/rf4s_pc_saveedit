#pragma once

#include "../config_data.h"
#include "../magic_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `MagicParam` overrides in all loaded mods and applies all changes found.
void apply_all_magic_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<MagicParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_magic_param_overrides(const toml::table& node, MagicParam& record);
} // namespace RFConfig
