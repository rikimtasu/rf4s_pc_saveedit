#pragma once

#include "../config_data.h"
#include "../monster_gift.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `MonsterGift` overrides in all loaded mods and applies all changes found.
void apply_all_monster_gift_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<MonsterGift>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_monster_gift_overrides(const toml::table& node, MonsterGift& record);
} // namespace RFConfig
