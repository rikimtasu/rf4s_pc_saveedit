#include "level_up_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../level_up.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_level_up_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<LevelUp>& config) {
    apply_all_overrides<LevelUp>(config, apply_level_up_overrides, mods, "level");
}

void apply_level_up_overrides(const toml::table& tbl, LevelUp& record) {
    read_override(tbl, "xp", record.xp);
    read_override(tbl, "hp", record.hp);
    read_override(tbl, "rp", record.rp);
    read_override(tbl, "strength", record.strength);
    read_override(tbl, "intelligence", record.intelligence);
    read_override(tbl, "vitality", record.vitality);
}
} // namespace RFConfig
