#pragma once

#include <cstdint>

namespace RFConfig {

// Weapon and armor abilities, stored in `EquipmentParam::gear_params`.
enum class GearFlags : uint32_t {
    None = 0,
    Fire = 0x00000001,               // Fire element
    Water = 0x00000002,              // Water element
    Earth = 0x00000004,              // Earth element
    Wind = 0x00000008,               // Wind element
    Light = 0x00000010,              // Light element
    Dark = 0x00000020,               // Dark element
    Love = 0x00000040,               // Love element
    Magic = 0x00000080,              // Magical attack, i.e. based on M.ATK/INT rather than ATK/STR. For waterpots.
    DirectPlayerDamage = 0x00000100, // Direct damage to player; declared in modkit, purpose unknown.
    IgnoreDefense = 0x00000200,      // Ignores DEF; declared in modkit, purpose unknown.
    NoSpread = 0x00000400,           // No random damage spread; declared in modkit, purpose unknown.
    HammerSound = 0x00000800,        // Plays a hammer sound on hit.
    FullStun = 0x00001000,           // Ignores stun and flinch resistance; hammers set this bit.
    TurnipEffect = 0x00002000,       // Shows the turnip and stars animation effect on hit.
    MarionettaGrab = 0x00008000,     // Performs the grab attack done by Marionetta.
    WaterSound = 0x00010000,         // Plays a wet/water sound on hit.
    DropRateUp = 0x00080000,         // Unconfirmed; no weapons seem to have this.
    WhiteStone = 0x00100000,         // Spouses/children receive half damage and deal 2x.
    MinimumDamage = 0x00200000,      // Scrap Metal + effect, every hit deals exactly 1 damage.
    HalfElementRes = 0x00400000,     // Halves element resistance
    FaintDropCabbage = 0x00800000,   // Fainted target drops Cabbage
    FaintDropPumpkin = 0x01000000,   // Fainted target drops Pumpkin
    FaintDropPotato = 0x02000000,    // Fainted target drops Potato
    FaintDropTurnip = 0x04000000,    // Fainted target drops Turnip
    MagnifyingGlass = 0x08000000,    // Shows detailed soil and crop information for the player's current tile.
    Lightweight = 0x20000000,        // Receive shield attribute bonuses (50%) with 2H weapons (dual blades, fists)
    NoCrits = 0x40000000,            // No critical hits
};

constexpr GearFlags operator|(GearFlags a, GearFlags b) {
    return static_cast<GearFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr GearFlags operator&(GearFlags a, GearFlags b) {
    return static_cast<GearFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr GearFlags operator~(GearFlags a) {
    return static_cast<GearFlags>(~static_cast<uint32_t>(a));
}

constexpr GearFlags& operator|=(GearFlags& a, GearFlags b) {
    return a = a | b;
}

constexpr GearFlags& operator&=(GearFlags& a, GearFlags b) {
    return a = a & b;
}

// Special effects of boots, stored in `EquipmentParam::boot_params`.
enum class BootFlags : uint32_t {
    None = 0,
    WaterWalking = 0x0001,        // Water Shoes: walk on water.
    AggroRangeDown = 0x0002,      // Sneaking Boots: reduces sight range for monsters to aggro.
    DashDistanceUp = 0x0004,      // Fast Step Boots: each dash covers more distance.
    FreeFarming = 0x0008,         // Free Farming Shoes: plant seeds anywhere, ignoring the grid.
    ChirpOnStep = 0x0010,         // Piyo Sandals: chirp with every step.
    BrakingSpeedDown = 0x0020,    // Ice Skates: slightly slower deceleration, i.e. a bit of "sliding".
    DashAttackDisabled = 0x0040,  // Step-In Boots: cannot perform dash attacks.
    BrakingSpeedUp = 0x0080,      // Snow Boots: faster deceleration, no sliding on icy terrain.
    Clumsy = 0x0100,              // Wet Boots: will trip and fall every so often (infrequent).
    HeightUp = 0x0200,            // Secret Shoes: very slightly increases the actor's height.
    MovementSpeedUp = 0x0400,     // Ghost Boots: slightly faster movement.
    MovementSpeedUpMore = 0x0800, // Rocket Wing: much faster movement.
    MovementSpeedDown = 0x1000,   // Iron Geta: slightly slower movement.
    ResistWeakWind = 0x2000,      // Heavy Boots: immune to a few, weak environmental winds, but not most.
    DashInvincibilityUp = 0x4000, // Strider Boots: longer invincibility frames when dashing.
};

constexpr BootFlags operator|(BootFlags a, BootFlags b) {
    return static_cast<BootFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr BootFlags operator&(BootFlags a, BootFlags b) {
    return static_cast<BootFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr BootFlags operator~(BootFlags a) {
    return static_cast<BootFlags>(~static_cast<uint32_t>(a));
}

constexpr BootFlags& operator|=(BootFlags& a, BootFlags b) {
    return a = a | b;
}

constexpr BootFlags& operator&=(BootFlags& a, BootFlags b) {
    return a = a & b;
}

// Special effects of accessories, stored in `EquipmentParam::acc_params`.
enum class AccessoryFlags : uint32_t {
    None = 0,
    DropRateUp = 0x0000001,         // Happy Ring: find more items.
    Poison = 0x0000002,             // Poison Ring: resist and inflict poison.
    Paralysis = 0x0000004,          // Paralysis Ring: resist and inflict paralysis.
    Seal = 0x0000008,               // Silent Ring: resist and inflict seal.
    ChargeSpeedUp = 0x0000010,      // Magic Ring: faster charging of staves and farm tools.
    ThrowDistanceUp = 0x0000020,    // Throwing Ring: throw items farther.
    MovementSpeedUp = 0x0000040,    // Anette's Necklace: increased movement speed.
    YawnDisabled = 0x0000080,       // Stay-up Ring: skip yawning animation at late hours. Still get fatigued.
    MonsterStatsUp = 0x0000100,     // Field Pendant: monster party members have increased stats.
    CompanionStatsUp = 0x0000200,   // Sun Pendant: human party members have increased stats.
    FarmToolAttackUp = 0x0000400,   // Dew Pendant: raises attack when equipped with a farm tool.
    LevelXpGainUp = 0x0000800,      // Star Pendant: gain more experience toward combat level.
    SkillXpGainUp = 0x0001000,      // Heart Pendant: gain more experience toward skill levels.
    RpCostDown = 0x0002000,         // Hand-Knit Scarf: half RP for uncharged tools, slight reduction otherwise.
    RpCostDownMore = 0x0004000,     // Fluffy Scarf: no RP for uncharged tools, moderate reduction otherwise.
    NullDamageChance = 0x0008000,   // Shield Ring: sometimes take only 1 damage
    BestAttack = 0x0010000,         // Magic Charm: use the stronger of ATK / M.ATK.
    MaxHpUp = 0x0020000,            // Champ Belt: raises max HP.
    NoMonsterSpawns = 0x0040000,    // Rosary: random monsters do not spawn, only bosses.
    ReverseStatus = 0x0080000,      // Talisman: reverses certain status effects (poison, paralyze, fatigue).
    HpRegen = 0x0100000,            // Hero's Proof: periodically recover a small amount of HP.
    RpRegen = 0x0200000,            // Proof of Wisdom: periodically recover a small amount of RP.
    FlinchTimeDown = 0x0400000,     // Art of Defense: reduced flinch time when hit by enemies.
    HitRangeUp = 0x0800000,         // Art of Attack: all weapons have increased attack range.
    PhysicalDamageDown = 0x1000000, // Art of Magic: halves non-elemental damage.
    RecoveryUp = 0x2000000,         // Earth Pendant: recovery items heal more.
    IgnoreDefense = 0x4000000,      // Strange Pendant: DEF/M.DEF on both character and enemies are ignored.
};

constexpr AccessoryFlags operator|(AccessoryFlags a, AccessoryFlags b) {
    return static_cast<AccessoryFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr AccessoryFlags operator&(AccessoryFlags a, AccessoryFlags b) {
    return static_cast<AccessoryFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr AccessoryFlags operator~(AccessoryFlags a) {
    return static_cast<AccessoryFlags>(~static_cast<uint32_t>(a));
}

constexpr AccessoryFlags& operator|=(AccessoryFlags& a, AccessoryFlags b) {
    return a = a | b;
}

constexpr AccessoryFlags& operator&=(AccessoryFlags& a, AccessoryFlags b) {
    return a = a & b;
}

// Stats for an equippable item.
//
// Game data includes records for all items, not only equipment. However, the values only seem to be meaningful for
// equipment (weapons, gear, shoes, accessories).
//
// Percentage fields are fixed-point, where 4096 = 100%.
//
// File: rf3ItemEquipmentParam.bin
struct EquipmentParam {
    // Weapon and armor abilities.
    GearFlags gear_params;

    // Special effects of boots.
    BootFlags boot_params;

    // Special effects of accessories.
    AccessoryFlags acc_params;

    // ATK rating; adds to physical damage.
    int32_t attack;

    // M.ATK rating; adds to magical damage, for both the weapon (if a staff) and magic skills.
    int32_t magic_attack;

    // DEF rating; reduces physical damage taken.
    int32_t defense;

    // M.DEF rating; reduces all elemental damage taken.
    int32_t magic_defense;

    // Bonus to the actor's STR; increases physical damage.
    int32_t strength;

    // Bonus to the actor's INT; increases magical damage.
    int32_t intelligence;

    // Bonus to the actor's VIT; reduces both physical and magical/element damage at half the rate per point as the
    // `defense` and `magic_defense` stats; i.e. 2 points of `vitality` is worth 1 point each of `defense` and
    // `magic_defense`.
    int32_t vitality;

    // Diz rating, weapons only; higher values cause monsters to be knocked out with fewer hits.
    int32_t dizzy;

    // Bonus to critical hit chance (%, additive).
    int32_t crit;

    // Bonus to distance enemies are knocked back on hit (%).
    int32_t knock;

    // Bonus to duration that enemies are stunned (%), once they hit the dizzy max.
    int32_t stun;

    // Chance to inflict poison on hit (%).
    int32_t poison_atk;

    // Chance to inflict seal on hit (%).
    int32_t seal_atk;

    // Chance to inflict paralysis on hit (%).
    int32_t paralysis_atk;

    // Chance to inflict sleep on hit (%).
    int32_t sleep_atk;

    // Chance to inflict fatigue on hit (%).
    int32_t fatigue_atk;

    // Chance to inflict sick on hit (%).
    int32_t sick_atk;

    // Chance to cause instant death on hit (%).
    int32_t faint_atk;

    // % of inflicted damage absorbed as HP.
    int32_t drain_atk;

    // Bonus to fire element resistance (%. additive).
    int32_t fire_res;

    // Bonus to water element resistance (%, additive).
    int32_t water_res;

    // Bonus to earth element resistance (%, additive).
    int32_t earth_res;

    // Bonus to wind element resistance (%, additive).
    int32_t wind_res;

    // Bonus to light element resistance (%, additive).
    int32_t light_res;

    // Bonus to dark element resistance (%, additive).
    int32_t dark_res;

    // Bonus to love element resistance (%, additive).
    int32_t love_res;

    // Physical (non-elemental) resistance or "no res" (%, additive).
    int32_t physical_res;

    // Reduction in received diz (knockout buildup) (%).
    //
    // Does not prevent being "launched" by some enemies, only the spinning-stars stun effect.
    int32_t dizzy_res;

    // Chance to cancel a received critical hit (%, additive).
    int32_t crit_res;

    // Reduction in knockback distance when hit by enemy (%, additive).
    int32_t knock_res;

    // Chance to resist a poison status infliction (%, additive).
    int32_t poison_res;

    // Chance to resist a seal status infliction (%, additive).
    int32_t seal_res;

    // Chance to resist a paralysis status infliction (%, additive).
    int32_t paralysis_res;

    // Chance to resist a sleep status infliction (%, additive).
    int32_t sleep_res;

    // Chance to resist a fatigue status infliction (%, additive).
    int32_t fatigue_res;

    // Chance to resist a sick status infliction (%, additive).
    int32_t sick_res;

    // Chance to resist an instant death attack (%, additive).
    int32_t faint_res;

    // Reduction in HP absorbed by some enemies as a % of their damage.
    int32_t drain_res;

    // Ambiguous, sometimes labeled as tool charge coverage (%) but is populated for all weapons and is usually a value
    // other than 100%. For armor pieces it is always 0.
    uint32_t depth;

    // Base attack range for a weapon, as % of the standard (short sword) distance.
    uint32_t hit_range;

    // Angle of the weapon's attack arc, as % of the standard (short sword) arc.
    uint32_t hit_arc;

    // Index of the weapon's model when held by an actor.
    //
    // Probably an offset into the `rom:/weapon` area starting at 0x3C61; shields start at value 0 and the first entry
    // here is `I_ShieldJ00.bfres`.
    uint32_t model;
};

static_assert(sizeof(EquipmentParam) == 0xB4);
} // namespace RFConfig
