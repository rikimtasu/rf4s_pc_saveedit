#pragma once

#include "../config_data.h"
#include "../item_use_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `ItemUseParam` overrides in all loaded mods and applies all changes found.
void apply_all_item_use_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<ItemUseParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_item_use_param_overrides(const toml::table& node, ItemUseParam& record);
} // namespace RFConfig
