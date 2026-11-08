#pragma once

#include <array>
#include <cstdint>

namespace RFConfig {

// Item price multipliers by item level.
//
// Records are indexed by `Item::buy_rate_index` and `Item::sell_rate_index`. An item's price at a given level is its
// base `Item::buy` or `Item::sell` price multiplied by the rate for that level.
//
// File: rf3PriceTable.bin
struct PriceTable {
    std::array<uint16_t, 10> rates; // 0x00 % of base price at levels 1 to 10 (100 = 100%)
};

static_assert(sizeof(PriceTable) == 0x14);
} // namespace RFConfig
