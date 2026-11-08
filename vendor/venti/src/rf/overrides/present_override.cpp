#include "present_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../present.h"
#include "override.h"

#include <array>
#include <string_view>
#include <vector>

namespace RFConfig {

constexpr auto kPresentGroupNames = std::to_array<std::string_view>({"dislikes", "likes", "loves"});

void apply_all_present_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                 ConfigFile<Present>& config) {
    apply_all_overrides<Present>(config, apply_present_overrides, mods, "present", partition_name, kPresentGroupNames);
}

void apply_present_overrides(const toml::table& node, Present& record) {
    read_override(node, "item", record.item);
    read_override(node, "fp", record.fp);
}
} // namespace RFConfig
