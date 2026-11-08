#include "monster_gift_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../monster_gift.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_monster_gift_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<MonsterGift>& config) {
    apply_all_overrides<MonsterGift>(config, apply_monster_gift_overrides, mods, "monster_gift");
}

void apply_monster_gift_overrides(const toml::table& node, MonsterGift& record) {
    read_override(node, "like_1", record.like_1);
    read_override(node, "fp_1", record.fp_1);
    read_override(node, "like_2", record.like_2);
    read_override(node, "fp_2", record.fp_2);
    read_override(node, "like_3", record.like_3);
    read_override(node, "fp_3", record.fp_3);
    read_override(node, "like_4", record.like_4);
    read_override(node, "fp_4", record.fp_4);
}
} // namespace RFConfig
