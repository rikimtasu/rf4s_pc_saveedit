#pragma once

#include "../config_data.h"
#include "../present.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

namespace RFConfig {

// Searches for `Present` overrides in all loaded mods and applies all changes found.
//
// `partition_name` is the lowercase, US-localized NPC name: vishnal, clorica, volkanon, etc.
void apply_all_present_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                 ConfigFile<Present>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_present_overrides(const toml::table& node, Present& record);
} // namespace RFConfig
