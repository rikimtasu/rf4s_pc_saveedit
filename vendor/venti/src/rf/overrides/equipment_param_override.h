#pragma once

#include "../config_data.h"
#include "../equipment_param.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `EquipmentParam` overrides in all loaded mods and applies all changes found.
void apply_all_equipment_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<EquipmentParam>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_equipment_param_overrides(const toml::table& node, EquipmentParam& record);
} // namespace RFConfig
