#include "present_category_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../present_category.h"
#include "override.h"

#include <array>
#include <string_view>
#include <vector>

namespace RFConfig {

// Group N is the category with ID 0x8100 + N.
// clang-format off
constexpr auto kPresentCategoryGroupNames = std::to_array<std::string_view>({
    "trash",
    "cakes",
    "sweets",
    "dumplings_misc",
    "jams_misc",
    "flowers",
    "medicines",
    "juices",
    "fruits",
    "milk",
    "rice_dishes",
    "bread_dishes",
    "tomato_dishes",
    "egg_dishes",
    "japanese_dishes",
    "cheese_dishes",
    "grape_dishes",
    "apple_dishes",
    "curry_dishes",
    "western_dishes",
    "chinese_dishes",
});
// clang-format on

void apply_all_present_category_overrides(const std::vector<Mods::LoadedMod>& mods,
                                          ConfigFile<PresentCategory>& config) {
    apply_all_overrides<PresentCategory>(config, apply_present_category_overrides, mods, "present_category", "",
                                         kPresentCategoryGroupNames);
}

void apply_present_category_overrides(const toml::table& node, PresentCategory& record) {
    read_override(node, "item", record.item);
    read_override(node, "fp", record.fp);
}
} // namespace RFConfig
