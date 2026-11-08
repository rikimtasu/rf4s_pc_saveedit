#pragma once

#include "../config_data.h"
#include "../present_category.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `PresentCategory` overrides in all loaded mods and applies all changes found.
void apply_all_present_category_overrides(const std::vector<Mods::LoadedMod>& mods,
                                          ConfigFile<PresentCategory>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_present_category_overrides(const toml::table& node, PresentCategory& record);
} // namespace RFConfig
