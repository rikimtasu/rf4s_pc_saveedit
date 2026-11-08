#include "price_table_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../price_table.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_price_table_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<PriceTable>& config) {
    apply_all_overrides<PriceTable>(config, apply_price_table_overrides, mods, "prices");
}

void apply_price_table_overrides(const toml::table& node, PriceTable& record) {
    read_override(node, "rates", record.rates);
}
} // namespace RFConfig
