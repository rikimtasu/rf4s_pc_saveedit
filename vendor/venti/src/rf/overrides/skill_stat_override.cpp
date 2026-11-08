#include "skill_stat_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../skill_stat.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_skill_stat_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<SkillStat>& config) {
    apply_all_overrides<SkillStat>(config, apply_skill_stat_overrides, mods, "skill_stat");
}

void apply_skill_stat_overrides(const toml::table& node, SkillStat& record) {
    read_override(node, "hp", record.hp);
    read_override(node, "rp", record.rp);
    read_override(node, "strength", record.strength);
    read_override(node, "intelligence", record.intelligence);
    read_override(node, "vitality", record.vitality);
    read_override(node, "attack", record.attack);
    read_override(node, "magic_attack", record.magic_attack);
    read_override(node, "resistance", record.resistance);
    read_override(node, "rp_reduction", record.rp_reduction);
}
} // namespace RFConfig
