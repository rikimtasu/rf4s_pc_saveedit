#pragma once

#include <cstdint>

namespace RFConfig {

// Gift preference for a single item or item category, according to a single NPC.
//
// Each character has a separate file, with three groups of records, in order: Dislikes, Likes, Loves.
//
// Files: rf3PresentNpc01.bin to rf3PresentNpc27.bin
struct Present {
    uint16_t item; // Item ID, or category ID (0x8000 and up; 0x8100 + N is `PresentCategory` group N)
    int16_t fp;    // Amount of FP gained when gifting this item.
};

static_assert(sizeof(Present) == 0x04);
} // namespace RFConfig
