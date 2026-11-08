#include "npc_param_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../npc_param.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_npc_param_overrides(const std::vector<Mods::LoadedMod>& mods, ConfigFile<NpcParam>& config) {
    apply_all_overrides<NpcParam>(config, apply_npc_param_overrides, mods, "npc");
}

void apply_npc_param_overrides(const toml::table& node, NpcParam& record) {
    read_override(node, "scale", record.scale);
    read_override(node, "collision_size", record.collision_size);
    read_override(node, "walk_speed", record.walk_speed);
    read_override(node, "run_speed", record.run_speed);
    read_override(node, "acceleration", record.acceleration);
    read_override(node, "braking", record.braking);
    read_override(node, "effect_scale", record.effect_scale);
    read_override(node, "height", record.height);
    read_override(node, "default_animation_set", record.default_animation_set);
    read_override(node, "ai_script", record.ai_script);
    read_override(node, "spawn_asleep_chance", record.spawn_asleep_chance);
    read_override(node, "base_hp", record.base_hp);
    read_override(node, "base_strength", record.base_strength);
    read_override(node, "base_intelligence", record.base_intelligence);
    read_override(node, "base_vitality", record.base_vitality);
    read_override(node, "xp", record.xp);
    read_override(node, "base_attack", record.base_attack);
    read_override(node, "base_magic_attack", record.base_magic_attack);
    read_override(node, "dizzy", record.dizzy);
    read_override(node, "base_defense", record.base_defense);
    read_override(node, "base_magic_defense", record.base_magic_defense);
    read_override(node, "strength_level_weight", record.strength_level_weight);
    read_override(node, "intelligence_level_weight", record.intelligence_level_weight);
    read_override(node, "vitality_level_weight", record.vitality_level_weight);
    read_override(node, "attack_level", record.attack_level);
    read_override(node, "magic_attack_level", record.magic_attack_level);
    read_override(node, "defense_level", record.defense_level);
    read_override(node, "magic_defense_level", record.magic_defense_level);
    read_override(node, "hp_level", record.hp_level);
    read_override(node, "dizzy_res", record.dizzy_res);
    read_override(node, "knock_atk", record.knock_atk);
    read_override(node, "stun_attack_duration", record.stun_attack_duration);
    read_override(node, "knock_res", record.knock_res);
    read_override(node, "stun_duration", record.stun_duration);
    read_override(node, "crit_atk", record.crit_atk);
    read_override(node, "crit_res", record.crit_res);
    read_override(node, "hit_arc", record.hit_arc);
    read_override(node, "hit_range", record.hit_range);
    read_override(node, "flying", record.flying);
    read_override(node, "fire_res", record.fire_res);
    read_override(node, "water_res", record.water_res);
    read_override(node, "earth_res", record.earth_res);
    read_override(node, "wind_res", record.wind_res);
    read_override(node, "light_res", record.light_res);
    read_override(node, "dark_res", record.dark_res);
    read_override(node, "physical_res", record.physical_res);
    read_override(node, "love_res", record.love_res);
    read_override(node, "poison_res", record.poison_res);
    read_override(node, "seal_res", record.seal_res);
    read_override(node, "paralysis_res", record.paralysis_res);
    read_override(node, "sleep_res", record.sleep_res);
    read_override(node, "fatigue_res", record.fatigue_res);
    read_override(node, "sick_res", record.sick_res);
    read_override(node, "faint_res", record.faint_res);
    read_override(node, "drain_res", record.drain_res);
    read_override(node, "drain_atk", record.drain_atk);
    read_override(node, "friendliness", record.friendliness);
    read_override(node, "movement_class", record.movement_class);
    read_override(node, "drop_item_1", record.drop_item_1);
    read_override(node, "drop_item_2", record.drop_item_2);
    read_override(node, "drop_item_3", record.drop_item_3);
    read_override(node, "drop_item_4", record.drop_item_4);
    read_override(node, "drop_chance_1", record.drop_chance_1);
    read_override(node, "drop_chance_2", record.drop_chance_2);
    read_override(node, "drop_chance_3", record.drop_chance_3);
    read_override(node, "drop_chance_4", record.drop_chance_4);
    read_override(node, "face_icon", record.face_icon);
    read_override(node, "rideable", record.rideable);
    read_override(node, "floating", record.floating);
    read_override(node, "model_set", record.model_set);
    read_override(node, "sight_range", record.sight_range);
    read_override(node, "sight_arc", record.sight_arc);
    read_override(node, "model", record.model);
    read_override(node, "animation_set", record.animation_set);
    read_override(node, "attack_set", record.attack_set);
    read_override(node, "ridden_attack_1", record.ridden_attack_1);
    read_override(node, "ridden_attack_1_alt", record.ridden_attack_1_alt);
    read_override(node, "ridden_attack_2", record.ridden_attack_2);
    read_override(node, "ridden_attack_2_alt", record.ridden_attack_2_alt);
    read_override(node, "ridden_attack_3", record.ridden_attack_3);
    read_override(node, "ridden_attack_3_alt", record.ridden_attack_3_alt);
    read_override(node, "base_level", record.base_level);
    read_override(node, "home_map", record.home_map);
    read_override(node, "slay_request_story_unlock", record.slay_request_story_unlock);
    read_override(node, "evs", record.evs);
    read_override(node, "produce", record.produce);
    read_override(node, "upgradable", record.upgradable);
    read_override(node, "produce_chance", record.produce_chance);
}
} // namespace RFConfig
