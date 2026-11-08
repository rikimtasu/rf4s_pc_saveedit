#include "fish_rate_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../fish_rate.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_fish_rate_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                   ConfigFile<FishRate>& config) {
    apply_all_overrides<FishRate>(config, apply_fish_rate_overrides, mods, "fish", partition_name);
}

void apply_fish_rate_overrides(const toml::table& node, FishRate& record) {
    read_override(node, "spring", record.spring);
    read_override(node, "spring_rain", record.spring_rain);
    read_override(node, "summer", record.summer);
    read_override(node, "summer_rain", record.summer_rain);
    read_override(node, "fall", record.fall);
    read_override(node, "fall_rain", record.fall_rain);
    read_override(node, "winter", record.winter);
    read_override(node, "winter_snow", record.winter_snow);
    read_override(node, "sand", record.sand);
    read_override(node, "idra_b2", record.idra_b2);
    read_override(node, "idra_b1", record.idra_b1);
    read_override(node, "yokmir_waterfall", record.yokmir_waterfall);
    read_override(node, "yokmir_pond", record.yokmir_pond);
    read_override(node, "water_ruins", record.water_ruins);
    read_override(node, "maya_road", record.maya_road);
    read_override(node, "sechs_cave", record.sechs_cave);
    read_override(node, "trash_0", record.trash_0);
    read_override(node, "trash_1", record.trash_1);
    read_override(node, "trash_2", record.trash_2);
    read_override(node, "trash_3", record.trash_3);
    read_override(node, "trash_4", record.trash_4);
    read_override(node, "level_rate_index", record.level_rate_index);
}
} // namespace RFConfig
