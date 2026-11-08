#pragma once

#include "../config_data.h"
#include "../item.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `Item` overrides in all loaded mods and applies all changes found.
void apply_all_item_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Item>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_item_overrides(const toml::table& node, Item& record);
} // namespace RFConfig
