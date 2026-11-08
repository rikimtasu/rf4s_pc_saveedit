#pragma once

#include <cstdint>

namespace RFConfig {

// Gifts liked by tameable monsters.
//
// File: rf3MonsterPresent.bin
struct MonsterGift {
    uint32_t like_1; // ID of the first liked item
    uint32_t fp_1;   // FP gained by giving `like_1`
    uint32_t like_2; // ID of the second liked item
    uint32_t fp_2;   // FP gained by giving `like_2`
    uint32_t like_3; // ID of the third liked item
    uint32_t fp_3;   // FP gained by giving `like_3`
    uint32_t like_4; // ID of the fourth liked item
    uint32_t fp_4;   // FP gained by giving `like_4`
};

static_assert(sizeof(MonsterGift) == 0x20);
} // namespace RFConfig
