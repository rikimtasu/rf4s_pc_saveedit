#pragma once

#include "../config_data.h"
#include "../npc_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `NpcParam` overrides in all loaded mods and applies all changes found.
void apply_all_npc_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<NpcParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_npc_param_overrides(const toml::table& node, NpcParam& record);
} // namespace RFConfig
