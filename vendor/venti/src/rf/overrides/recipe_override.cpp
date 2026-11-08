#include "recipe_override.h"

#include "../../mods/mod.h"
#include "../config_data.h"
#include "../recipe.h"
#include "override.h"

#include <vector>

namespace RFConfig {

void apply_all_recipe_overrides(const std::vector<Mods::LoadedMod>& mods, const char* partition_name,
                                ConfigFile<Recipe>& config) {
    apply_all_overrides<Recipe>(config, apply_recipe_overrides, mods, "recipe", partition_name);
}

void apply_recipe_overrides(const toml::table& node, Recipe& record) {
    read_override(node, "result", record.result);
    read_override(node, "material_1", record.material_1);
    read_override(node, "material_2", record.material_2);
    read_override(node, "material_3", record.material_3);
    read_override(node, "material_4", record.material_4);
    read_override(node, "material_5", record.material_5);
    read_override(node, "material_6", record.material_6);
    read_override(node, "level", record.level);
    read_override(node, "learned_flag_id", record.learned_flag_id);
}
} // namespace RFConfig
