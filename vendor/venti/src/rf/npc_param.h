#pragma once

#include <cstdint>

namespace RFConfig {

// Base stats, resistances and drops for NPCs and monsters.
//
// Percentage fields are fixed-point, where 4096 = 100%, unless otherwise noted, and except in the case of the `_level`
// fields where the percentage value seems to be the integer value itself.
//
// File: rf3NpcParam.bin
struct NpcParam {
    // Size (%) of the NPC's sprite in the field.
    int32_t scale;

    // Size used for collisions, where 16 = 100%.
    int32_t collision_size;

    // Walking speed, as a % of the game's default.
    int32_t walk_speed;

    // Running speed, as a % of the game's default.
    int32_t run_speed;

    // Rate of acceleration to top speed, as a % of the game's default.
    int32_t acceleration;

    // Rate of deceleration to stop, as a % of the game's default.
    int32_t braking;

    // Scale (%) of visual effects such as the break/death animation.
    int32_t effect_scale;

    // Literally the NPC height, e.g. affecting where the head is drawn.
    int32_t height;

    // Which animation set to use if `animation_set` is not defined; 0 = female, 1 = male.
    uint16_t default_animation_set;

    // Index of the script file (`AI_m`) governing this NPC's AI behavior.
    uint16_t ai_script;

    // Chance that when the NPC spawns, it will be asleep; max = 255 (100%).
    int32_t spawn_asleep_chance;

    // Max HP at level 1.
    int32_t base_hp;

    // STR at level 1.
    int32_t base_strength;

    // INT at level 1.
    int32_t base_intelligence;

    // VIT at level 1.
    int32_t base_vitality;

    // XP awarded to the player/party on kill.
    int32_t xp;

    // ATK at level 1.
    int32_t base_attack;

    // M.ATK at level 1.
    int32_t base_magic_attack;

    // Diz inflicted per hit; higher numbers lead to quicker knockouts after many hits.
    int32_t dizzy;

    // DEF at level 1.
    int32_t base_defense;

    // M.DEF at level 1.
    int32_t base_magic_defense;

    // Weighting of STR, relative to the INT and VIT weights, when a stat point is allocated during level up.
    //
    // For reasons known only to the original game devs, STR/INT/VIT follow different rules from other stats (ATK etc.).
    // First, a certain number of stat points are allocated, minimum of 9 plus a random bonus. Then, point by point,
    // each is assigned to one of the three stats, using an additional random roll compared against those weights.
    //
    // Although the weights have very similar values in the game data to the other `_level` fields, and look like a
    // % growth, their absolute values don't mean anything, they are just relative to each other.
    int32_t strength_level_weight;

    // Weighting of INT, relative to the STR and VIT weights, when a stat point is allocated during level up.
    //
    // See `strength_level_weight` for details on point assignment.
    int32_t intelligence_level_weight;

    // Weighting of VIT, relative to the STR and INT weights, when a stat point is allocated during level up.
    //
    // See `strength_level_weight` for details on point assignment.
    int32_t vitality_level_weight;

    // ATK gained per level, as a % of the game's default growth.
    int32_t attack_level;

    // M.ATK gained per level, as a % of the game's default growth.
    int32_t magic_attack_level;

    // DEF gained per level, as a % of the game's default growth.
    int32_t defense_level;

    // M.DEF gained per level, as a % of the game's default growth.
    int32_t magic_defense_level;

    // Max HP gained per level, as a % of the game's default growth.
    int32_t hp_level;

    // Percent reduction in the player/party's dizzy attack (stun buildup).
    int32_t dizzy_res;

    // Amount of knockback this NPC applies to others when landing a hit.
    int32_t knock_atk;

    // Duration of the stun (% of game's default) when this NPC stuns a target.
    int32_t stun_attack_duration;

    // Reduction (%) in knockback distance when hit by player/party.
    int32_t knock_res;

    // Duration that the stun lasts when this NPC becomes stunned (i.e. reaching `dizzy_max`).
    int32_t stun_duration;

    // Critical hit rate (%) when this NPC is attacking.
    int32_t crit_atk;

    // Critical hit resistance (%) when attacked.
    int32_t crit_res;

    // Roughly, the "hitbox width" of the NPC's attack, but applied as an arc, with 65536 = 360 degrees.
    // Affects how wide, but not how far, the attack can cover.
    uint16_t hit_arc;

    // Roughly, the "hitbox length/distance", i.e. distance out from which the NPC's attacks extend along the `hit_arc`.
    // Higher values mean attacks hit actors farther away.
    uint16_t hit_range;

    // Set for all flying monsters but does not have a known effect.
    int32_t flying;

    // Apparently unused field, never read by the game.
    int32_t unknown_94;

    // Resistance (%) to fire element attacks.
    int32_t fire_res;

    // Resistance (%) to water element attacks.
    int32_t water_res;

    // Resistance (%) to earth element attacks.
    int32_t earth_res;

    // Resistance (%) to wind element attacks.
    int32_t wind_res;

    // Resistance (%) to light element attacks.
    int32_t light_res;

    // Resistance (%) to dark element attacks.
    int32_t dark_res;

    // Resistance (%) to physical attacks. The in-game text is "No Res", i.e. Non-Elemental Resistance.
    int32_t physical_res;

    // Resistance (%) to love element attacks.
    int32_t love_res;

    // Resistance (%) to being poisoned.
    int32_t poison_res;

    // Resistance (%) to being sealed (unable to use magic).
    int32_t seal_res;

    // Resistance (%) to being paralyzed (slow movement).
    int32_t paralysis_res;

    // Resistance (%) to being put to sleep.
    int32_t sleep_res;

    // Resistance (%) to being fatigued.
    int32_t fatigue_res;

    // Resistance (%) to sick status.
    int32_t sick_res;

    // Resistance (%) to faint, i.e. instant death.
    int32_t faint_res;

    // Resistance (%) to drain (HP absorb) attacks. Modifies the % of HP recovered by the attacker.
    int32_t drain_res;

    // Assumed to be natural HP absorb (% of damage) on attack, but not used on any party-able NPCs or recruitable
    // monsters. May or may not work as expected.
    int32_t drain_atk;

    // Tameability; higher numbers = more likely to befriend per each item given.
    int32_t friendliness;

    // Affects the NPC's movement, exact details still unclear.
    int32_t movement_class;

    // ID of the first item potentially dropped on kill.
    uint16_t drop_item_1;

    // ID of the second item potentially dropped on kill.
    uint16_t drop_item_2;

    // ID of the third item potentially dropped on kill.
    uint16_t drop_item_3;

    // ID of the fourth item potentially dropped on kill.
    uint16_t drop_item_4;

    // Chance (%) to drop the `drop_item_1`, where 1000 = 100%.
    int32_t drop_chance_1;

    // Chance (%) to drop the `drop_item_2`, where 1000 = 100%.
    int32_t drop_chance_2;

    // Chance (%) to drop the `drop_item_3`, where 1000 = 100%.
    int32_t drop_chance_3;

    // Chance (%) to drop the `drop_item_4`, where 1000 = 100%.
    int32_t drop_chance_4;

    // ID of the face icon to display for this NPC in the game's UI.
    uint16_t face_icon;

    // Whether the tamed NPC can be mounted by the player; 0 = no, 1 = yes.
    uint8_t rideable;

    // Whether the NPC can float over water and low obstacles; 0 = no, 1 = yes.
    //
    // This field appears to track the `flying` field's data but is the one that is actually used for collisions.
    uint8_t floating;

    // Identifies a family of similar NPCs used for loading models/skeletons.
    //
    // Although the actual value does tend to group together monsters with the same model--such as Shadow Panther and
    // Blood Panther, or Buffaloo and Buffamoo--this tends to act more like a general "model type" and the exact value
    // does not really matter so much as the range in which it falls:
    // - All values between 48-253 treat the `model` as an index starting from 0x3128, the first `rom:/mons` entry, i.e.
    //   a monster model.
    // - Other values treat the `model` as an index starting from 0x03A5, the first `rom:/chr` entry, i.e. a character.
    //   This includes actual characters but also inanimate objects like signs and furniture, which also happen to
    //   appear in the "character" list, but have values >= 254 for this field which triggers special behavior.
    //
    // An additional property is that when a monster is spawned, a value of 0 causes the model to load with different
    // parameters, probably as static rather than animated, since it largely applies to furniture and other inanimate
    // objects. This _only_ applies to monster spawns; character spawns are done in an entirely different place and
    // always use animated models.
    //
    // These ranges are hard-coded in the game, and no evidence has been found that the value within the range makes any
    // difference. Thus:
    // - Major characters (non monsters) can have any value below 48, usually zero. Non-zero values (Blossom = 16) might
    //   indicate they can also be spawned as a "monster" in some event.
    // - Monsters can have any value between 48 and 253.
    // - Static objects usually have a value of 0, except those with values >= 254 which have special (hard-coded)
    //   behavior; don't use the high range unless you know what you're doing.
    int32_t model_set;

    // How far the actor can see, i.e. aggro distance along the `sight_arc`. Works similarly to the `hit_range` but
    // applied to their vision and not their attacks.
    int32_t sight_range;

    // The actor's vision code or field of view, where 65536 = 360 degrees. Party members inside this arc and within
    // the `sight_range` will cause aggro.
    uint32_t sight_arc;

    // Apparently unused; values never read by the game.
    uint32_t unknown_10c;

    // Index of the model asset, which is added to the model set offset (0x03A5 for characters, 0x3128 for monsters) to
    // get the asset ID for the actor model. The value `0` is a real model; `-1` means no model.
    //
    // While the manifest lists names with `.bfres` extension, which is a Nintendo archive format used with Switch, on
    // PC these are a different, custom format containing similar data (geometry, skeleton, textures, etc.).
    //
    // In a dump of the main bundle, these are the assets named `NPC_*.model` (characters), `BM_*.model` or `M_*.model`
    // (monsters).
    int16_t model;

    // Index of the first skeletal animation asset, which is always added to offset 0x3128 to get the asset ID for the
    // actor's animations.
    //
    // Only monster animation sets (`M_` and `BM_` files) exist as assets; unlike `model`, there is no separate category
    // for human characters. The value `-1` means no animation, and most characters use that value, except one, which
    // can also spawn as a monster. A value of `0` would point to a real animation.
    //
    // These are both listed and dumped as `.bfskl` files, but actually appear to be `.bfres` containers each with only
    // a single animation and no other data.
    int16_t animation_set;

    // Apparently unused; values never read by the game.
    uint32_t unknown_114;

    // Index offset of the attack set used by this actor.
    //
    // Although not confirmed by decompilation, this is most likely added to 0x00F3 (beginning of the `rom:/as` entries)
    // to get the asset ID, which for monsters will typically land on an `as_atk_mb_*` or `as_atk_m_*` file. For
    // example, Orc has value 0x196, which adds up to 0x289, the ID of the first monster attack, `as_atk_m_00_00.bin`.
    //
    // Characters always have 0 in this field unless they can also spawn as monsters.
    uint16_t attack_set;

    // Index of the primary attack to perform when ridden by the player.
    //
    // This is likely applied as an offset to the entry identified by `attack_set`. For example, if the first attack is
    // `as_atk_m_06_00.bin`, and the value of this field is 0x7, then the attack used will be `as_atk_m_06_07.bin`.
    //
    // Note that different NPCs do not have equal numbers of attack scripts. The value used for this field must be valid
    // for the specific NPC and only has meaning for that NPC.
    uint8_t ridden_attack_1;

    // Alternate version of the primary mounted attack, applied when thrown (?). Usually the same as `ridden_attack_1`.
    uint8_t ridden_attack_1_alt;

    // Index of the secondary attack to perform when ridden by the player.
    //
    // See `ridden_attack_1` for implementation details.
    uint8_t ridden_attack_2;

    // Alternate version of the secondary mounted attack. See `ridden_attack_1_alt` for implementation details.
    uint8_t ridden_attack_2_alt;

    // Index of the tertiary attack to perform when ridden by the player.
    //
    // See `ridden_attack_1` for implementation details.
    uint8_t ridden_attack_3;

    // Alternate version of the tertiary mounted attack. See `ridden_attack_1_alt` for implementation details.
    uint8_t ridden_attack_3_alt;

    // Default level of the monster when spawned. Actual level may be modified by game flags, area, etc.
    int32_t base_level;

    // ID of the map that the game considers to be the monster's earliest or most common spawning area.
    //
    // This is the area that Eliza requests to kill the monster will point the player to; see
    // `slay_request_story_unlock`.
    uint16_t home_map;

    // Story progress required before Eliza requests will appear to kill this type of monster.
    uint16_t slay_request_story_unlock;

    // Effort Values for this monster, named after the Pokemon concept. Low to high bytes are HP, STR, INT, VIT.
    //
    // Tamed monsters initially have 50 points to distribute among the four stats, which ultimately become percentage
    // bonuses, with HP values counting as double. When the player kills a monster of this type, with a tamed monster in
    // his/her party, then that tamed monster will gain these points as percentage bonuses, until all 50 points have
    // been assigned.
    //
    // For example, if the player, with a tamed monster in the party, kills 25 Buffaloos (EV: +1 STR) and 25 Ants
    // (EV: +1 HP) then the tamed monster ends up with a permanent bonus of +25% STR and +50% HP, and no more points can
    // be assigned with additional kills.
    //
    // Most of the time, regular monsters will provide +1 or +2 to a single stat. +3 or higher in a single stat, or
    // non-zero values in multiple stats, are comparatively rare, although they are perfectly legal.
    uint32_t evs;

    // ID of the item that a tamed version of the monster will drop as produce in the barn.
    uint32_t produce;

    // Whether the `produce` gains size at higher monster levels, e.g. Medium or Large milk for Buffamoos.
    //
    // This is a boolean value, with 0 = No, 1 = Yes.
    uint8_t upgradable;

    // Chance that a tamed monster will drop its `produce` on any given day; 255 = 100%.
    uint8_t produce_chance;

    // May be used by the game, but its purpose is still unknown.
    int16_t unknown_132;
};

static_assert(sizeof(NpcParam) == 0x134);
} // namespace RFConfig
