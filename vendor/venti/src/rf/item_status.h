#pragma once

#include <cstdint>

namespace RFConfig {

// Status ailments healed or caused by using an item.
enum class ItemStatusFlags : uint32_t {
    None = 0,
    HealPoison = 0x0001,
    HealSeal = 0x0002,
    HealParalysis = 0x0004,
    HealSleep = 0x0008,
    HealFatigue = 0x0010,
    HealSick = 0x0020,
    CausePoison = 0x0040,
    CauseSeal = 0x0080,
    CauseParalysis = 0x0100,
    CauseSleep = 0x0200,
    CauseFatigue = 0x0400,
    CauseSick = 0x0800,
    CauseFaint = 0x1000,
    LevelUp = 0x2000,
    Unknown4000 = 0x4000, // Only seen in `Upgrade::status_cook`, where most records have it.
};

constexpr ItemStatusFlags operator|(ItemStatusFlags a, ItemStatusFlags b) {
    return static_cast<ItemStatusFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

constexpr ItemStatusFlags operator&(ItemStatusFlags a, ItemStatusFlags b) {
    return static_cast<ItemStatusFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

constexpr ItemStatusFlags operator~(ItemStatusFlags a) {
    return static_cast<ItemStatusFlags>(~static_cast<uint32_t>(a));
}

constexpr ItemStatusFlags& operator|=(ItemStatusFlags& a, ItemStatusFlags b) {
    return a = a | b;
}

constexpr ItemStatusFlags& operator&=(ItemStatusFlags& a, ItemStatusFlags b) {
    return a = a & b;
}
} // namespace RFConfig