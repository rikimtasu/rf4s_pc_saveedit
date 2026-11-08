#include "geode_rate_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../geode_rate.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_geode_rate_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<GeodeRate>& config) {
    apply_all_overrides<GeodeRate>(config, apply_geode_rate_overrides, mods, "geode");
}

void apply_geode_rate_overrides(const toml::table& node, GeodeRate& record) {
    read_override(node, "kind", record.kind);
    read_override(node, "break_chance", record.break_chance);
    read_override(node, "scrap_chance", record.scrap_chance);
    read_override(node, "drop_weight_1", record.drop_weight_1);
    read_override(node, "drop_weight_2", record.drop_weight_2);
    read_override(node, "drop_weight_3", record.drop_weight_3);
    read_override(node, "drop_item_1", record.drop_item_1);
    read_override(node, "drop_item_2", record.drop_item_2);
    read_override(node, "drop_item_3", record.drop_item_3);
    read_override(node, "drop_item_rare", record.drop_item_rare);
}
} // namespace RFConfig
