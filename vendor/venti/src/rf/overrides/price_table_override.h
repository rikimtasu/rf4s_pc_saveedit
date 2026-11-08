#pragma once

#include "../config_data.h"
#include "../price_table.h"

#include "../../mods/mod.h"

#include <toml++/toml.hpp>

#include <vector>

namespace RFConfig {

// Searches for `PriceTable` overrides in all loaded mods and applies all changes found.
void apply_all_price_table_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<PriceTable>& config);

// Replaces fields of `record` with any values present in `node`, leaving the rest unchanged.
void apply_price_table_overrides(const toml::table& node, PriceTable& record);
} // namespace RFConfig
