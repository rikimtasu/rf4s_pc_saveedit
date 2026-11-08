#pragma once

#include <cstdint>

namespace RFConfig {

// Level distributions for different types of fish.
//
// The configuration contains 10 records, one per fish level, with each column (probably?) representing a different
// category (type) of fish.
//
// Files: Fishing_rate_lv_Spring.bin, Fishing_rate_lv_Spring2.bin
struct FishLevelRate {
    // Level weights for fish in category 0.
    uint32_t type_0;

    // Level weights for fish in category 1.
    uint32_t type_1;

    // Level weights for fish in category 2.
    uint32_t type_2;

    // Level weights for fish in category 3.
    uint32_t type_3;
};

static_assert(sizeof(FishLevelRate) == 0x10);
} // namespace RFConfig
