#pragma once

#include "../config_data.h"
#include "../recipe.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

namespace RFConfig {

// Searches for `Recipe` overrides in all loaded mods and applies all changes found.
//
// `partition_name` is the recipe category such as `accessory`, `short_sword` or `frying_pan`.
void apply_all_recipe_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                ConfigFile<Recipe>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_recipe_overrides(const toml::table& node, Recipe& record);
} // namespace RFConfig
