#include "fish_level_rate_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../fish_level_rate.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_fish_level_rate_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                         ConfigFile<FishLevelRate>& config) {
    apply_all_overrides<FishLevelRate>(config, apply_fish_level_rate_overrides, mods, "fish_level", partition_name);
}

void apply_fish_level_rate_overrides(const toml::table& node, FishLevelRate& record) {
    read_override(node, "type_0", record.type_0);
    read_override(node, "type_1", record.type_1);
    read_override(node, "type_2", record.type_2);
    read_override(node, "type_3", record.type_3);
}
} // namespace RFConfig
