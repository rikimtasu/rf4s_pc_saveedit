#pragma once

#include <cstdint>

namespace RFConfig {

// Gift preference for a single item within a gift category.
//
// Each category is a separate group of records. A character's `Present` entry with the category ID 0x8100 + N refers to
// group N, in order:
// - 0x00 Trash
// - 0x01 Cakes
// - 0x02 Sweets
// - 0x03 Pound Cake and Dumplings
// - 0x04 Sweet Breads and Jams
// - 0x05 Flowers
// - 0x06 Medicines
// - 0x07 Juices
// - 0x08 Fruits
// - 0x09 Milk
// - 0x0A Rice Dishes
// - 0x0B Bread Dishes
// - 0x0C Tomato Dishes
// - 0x0D Egg Dishes
// - 0x0E Japanese Dishes
// - 0x0F Cheese Dishes
// - 0x10 Grape Dishes
// - 0x11 Apple Dishes
// - 0x12 Curry Dishes
// - 0x13 Western Dishes
// - 0x14 Chinese Dishes
//
// File: rf3PresentCategory.bin
struct PresentCategory {
    uint16_t item; // 0x00 Item ID
    int16_t fp;    // 0x02 Default amount of FP gained when gifting this item.
};

static_assert(sizeof(PresentCategory) == 0x04);
} // namespace RFConfig
