#include "crop_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../crop.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_crop_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<Crop>& config) {
    apply_all_overrides<Crop>(config, apply_crop_overrides, mods, "crop");
}

void apply_crop_overrides(const toml::table& node, Crop& record) {
    read_override(node, "stage_1_days", record.stage_1_days);
    read_override(node, "stage_2_days", record.stage_2_days);
    read_override(node, "stage_3_days", record.stage_3_days);
    read_override(node, "stage_4_days", record.stage_4_days);
    read_override(node, "stage_1_size", record.stage_1_size);
    read_override(node, "stage_2_size", record.stage_2_size);
    read_override(node, "stage_3_size", record.stage_3_size);
    read_override(node, "stage_4_size", record.stage_4_size);
    read_override(node, "giant_sprite_size", record.giant_sprite_size);
    read_override(node, "withered_sprite_size", record.withered_sprite_size);
    read_override(node, "wild_spawn_chance", record.wild_spawn_chance);
    read_override(node, "initial_hp", record.initial_hp);
    read_override(node, "collision_size", record.collision_size);
    read_override(node, "regrowth_days", record.regrowth_days);
    read_override(node, "yield", record.yield);
    read_override(node, "defense", record.defense);
    read_override(node, "harvest_event_chance", record.harvest_event_chance);
    read_override(node, "harvest_health_cost", record.harvest_health_cost);
    read_override(node, "soil_xp_overall", record.soil_xp_overall);
    read_override(node, "soil_xp_speed", record.soil_xp_speed);
    read_override(node, "soil_xp_quality", record.soil_xp_quality);
    read_override(node, "soil_xp_size", record.soil_xp_size);
    read_override(node, "soil_xp_yield", record.soil_xp_yield);
    read_override(node, "growth_rate", record.growth_rate);
    read_override(node, "quality_gain_rate", record.quality_gain_rate);
    read_override(node, "size_gain_rate", record.size_gain_rate);
    read_override(node, "yield_gain_rate", record.yield_gain_rate);
    read_override(node, "harvest_growth_cost", record.harvest_growth_cost);
    read_override(node, "harvest_quality_cost", record.harvest_quality_cost);
    read_override(node, "harvest_size_cost", record.harvest_size_cost);
    read_override(node, "harvest_yield_cost", record.harvest_yield_cost);
    read_override(node, "harvest_item", record.harvest_item);
    read_override(node, "seed_item", record.seed_item);
    read_override(node, "flags", record.flags);
}
} // namespace RFConfig
