#include "item_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../item.h"
#include "override.h"

#include <cstdint>
#include <vector>

namespace RFConfig {

void apply_all_item_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Item>& config) {
    apply_all_overrides<Item>(config, apply_item_overrides, mods, "item");
}

void apply_item_overrides(const toml::table& node, Item& record) {
    read_override(node, "family", record.family);
    read_override(node, "category", record.category);
    read_nibble_override(node, "rarity", [&](uint8_t value) { record.set_rarity(value); });
    read_nibble_override(node, "max_stack", [&](uint8_t value) { record.set_max_stack(value); });
    read_override(node, "buy_rate_index", record.buy_rate_index);
    read_override(node, "sell_rate_index", record.sell_rate_index);
    read_override(node, "buy", record.buy);
    read_override(node, "sell", record.sell);
    read_override(node, "crop", record.crop);
    read_override(node, "flags", record.flags);
    read_override(node, "story_unlock", record.story_unlock);
    read_override(node, "sort_order", record.sort_order);
    read_override(node, "staff_shot_level", record.staff_shot_level);
}
} // namespace RFConfig
