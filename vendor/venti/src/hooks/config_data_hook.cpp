#include "config_data_hook.h"

#include "../address.h"
#include "../mods/mod.h"
#include "../rf/config_data.h"
#include "../rf/overrides/crop_override.h"
#include "../rf/overrides/equipment_param_override.h"
#include "../rf/overrides/fish_level_rate_override.h"
#include "../rf/overrides/fish_rate_override.h"
#include "../rf/overrides/geode_rate_override.h"
#include "../rf/overrides/item_override.h"
#include "../rf/overrides/item_use_param_override.h"
#include "../rf/overrides/level_up_override.h"
#include "../rf/overrides/magic_param_override.h"
#include "../rf/overrides/monster_gift_override.h"
#include "../rf/overrides/npc_param_override.h"
#include "../rf/overrides/present_category_override.h"
#include "../rf/overrides/present_override.h"
#include "../rf/overrides/price_table_override.h"
#include "../rf/overrides/recipe_override.h"
#include "../rf/overrides/skill_data_param_override.h"
#include "../rf/overrides/skill_exp_param_override.h"
#include "../rf/overrides/skill_stat_override.h"
#include "../rf/overrides/upgrade_override.h"

#include "plog/Log.h"

#include <safetyhook.hpp>

#include <cstddef>
#include <cstdint>
#include <exception>
#include <functional>
#include <vector>

namespace ConfigDataHook {

namespace {

    using namespace RFConfig;

    SafetyHookMid g_load_asset_hook{};

    // Applies all loaded mods' overrides to a config file's data, given its size in bytes.
    using OverrideApplier = std::function<void(const std::vector<Mods::LoadedMod>& mods, void* data, size_t size)>;

    // Creates an applier for a config type stored in a single file. `raw` is true for files without an NLCL header.
    template <typename T>
    OverrideApplier make_applier(void (*apply_all)(const std::vector<Mods::LoadedMod>&, ConfigFile<T>&),
                                 bool raw = false) {
        return [apply_all, raw](const std::vector<Mods::LoadedMod>& mods, void* data, size_t size) {
            auto config = ConfigFile<T>::overlay(data, size, raw);
            apply_all(mods, config);
        };
    }

    // Creates an applier for one file of a config type that is spread across multiple files.
    template <typename T>
    OverrideApplier make_applier(void (*apply_all)(const std::vector<Mods::LoadedMod>&, const char*, ConfigFile<T>&),
                                 const char* partition_name) {
        return [apply_all, partition_name](const std::vector<Mods::LoadedMod>& mods, void* data, size_t size) {
            auto config = ConfigFile<T>::overlay(data, size);
            apply_all(mods, partition_name, config);
        };
    }

    // Gets the override applier for an archive file, or an empty function if the file has no supported overrides.
    OverrideApplier get_override_applier(uint32_t file_index) {
        switch (file_index) {
            case 4877: // MapOre_Rate.bin
                return make_applier(apply_all_geode_rate_overrides);
            case 14803: // Fishing_rate_fish_Spring.bin
                return make_applier(apply_all_fish_rate_overrides, "spring");
            case 14804: // Fishing_rate_fish_Spring2.bin
                return make_applier(apply_all_fish_rate_overrides, "spring2");
            case 14805: // Fishing_rate_lv_Spring.bin
                return make_applier(apply_all_fish_level_rate_overrides, "spring");
            case 14806: // Fishing_rate_lv_Spring2.bin
                return make_applier(apply_all_fish_level_rate_overrides, "spring2");
            case 14807: // rf3CropParam.bin
                return make_applier(apply_all_crop_overrides);
            case 14808: // rf3ItemEquipmentParam.bin
                return make_applier(apply_all_equipment_param_overrides);
            case 14809: // rf3ItemList.bin
                return make_applier(apply_all_item_overrides);
            case 14811: // rf3ItemStrengthening.bin
                return make_applier(apply_all_upgrade_overrides);
            case 14812: // rf3NpcParam.bin
                return make_applier(apply_all_npc_param_overrides);
            case 14813: // rf3Parameter.bin
                return make_applier(apply_all_level_up_overrides);
            case 14817: // rf3ParamMagic.bin
                return make_applier(apply_all_magic_param_overrides);
            case 14818: // rf3ParamSkill.bin
                return make_applier(apply_all_skill_stat_overrides);
            case 14819: // rf3ParamSkillData.bin
                return make_applier(apply_all_skill_data_param_overrides);
            case 14820: // rf3ParamSkillExp.bin
                return make_applier(apply_all_skill_exp_param_overrides, "combat");
            case 14821: // rf3ParamSkillExpFarm.bin
                return make_applier(apply_all_skill_exp_param_overrides, "tools");
            case 14822: // rf3ParamSkillExpFish.bin
                return make_applier(apply_all_skill_exp_param_overrides, "field");
            case 14823: // rf3ParamSkillExpMix.bin
                return make_applier(apply_all_skill_exp_param_overrides, "synthesis");
            case 14824: // rf3ParamSkillExpSleep.bin
                return make_applier(apply_all_skill_exp_param_overrides, "lifestyle");
            case 14825: // rf3PriceTable.bin
                return make_applier(apply_all_price_table_overrides);
            case 14826: // rf3RecipeAcce.bin
                return make_applier(apply_all_recipe_overrides, "accessory");
            case 14827: // rf3RecipeArmor.bin
                return make_applier(apply_all_recipe_overrides, "armor");
            case 14828: // rf3RecipeCookFry.bin
                return make_applier(apply_all_recipe_overrides, "frying_pan");
            case 14829: // rf3RecipeCookHandmade.bin
                return make_applier(apply_all_recipe_overrides, "handmade");
            case 14830: // rf3RecipeCookKnife.bin
                return make_applier(apply_all_recipe_overrides, "knife");
            case 14831: // rf3RecipeCookMixer.bin
                return make_applier(apply_all_recipe_overrides, "mixer");
            case 14832: // rf3RecipeCookOven.bin
                return make_applier(apply_all_recipe_overrides, "oven");
            case 14833: // rf3RecipeCookPan.bin
                return make_applier(apply_all_recipe_overrides, "pot");
            case 14834: // rf3RecipeCookSteamer.bin
                return make_applier(apply_all_recipe_overrides, "steamer");
            case 14835: // rf3RecipeDrug.bin
                return make_applier(apply_all_recipe_overrides, "chemistry");
            case 14836: // rf3RecipeFarm.bin
                return make_applier(apply_all_recipe_overrides, "tool");
            case 14837: // rf3RecipeHat.bin
                return make_applier(apply_all_recipe_overrides, "headgear");
            case 14838: // rf3RecipeShield.bin
                return make_applier(apply_all_recipe_overrides, "shield");
            case 14839: // rf3RecipeShoes.bin
                return make_applier(apply_all_recipe_overrides, "shoes");
            case 14840: // rf3RecipeWeaponA.bin
                return make_applier(apply_all_recipe_overrides, "short_sword");
            case 14841: // rf3RecipeWeaponB.bin
                return make_applier(apply_all_recipe_overrides, "long_sword");
            case 14842: // rf3RecipeWeaponC.bin
                return make_applier(apply_all_recipe_overrides, "spear");
            case 14843: // rf3RecipeWeaponD.bin
                return make_applier(apply_all_recipe_overrides, "axe_hammer");
            case 14844: // rf3RecipeWeaponE.bin
                return make_applier(apply_all_recipe_overrides, "weapon_e");
            case 14845: // rf3RecipeWeaponK.bin
                return make_applier(apply_all_recipe_overrides, "staff");
            case 14846: // rf3RecipeWeaponM.bin
                return make_applier(apply_all_recipe_overrides, "dual_blade");
            case 14847: // rf3RecipeWeaponN.bin
                return make_applier(apply_all_recipe_overrides, "fist");
            case 14848: // rf3UseItemParam.bin
                return make_applier(apply_all_item_use_param_overrides);
            case 14849: // rf3MonsterPresent.bin
                return make_applier(apply_all_monster_gift_overrides, true);
            case 14850: // rf3PresentCategory.bin
                return make_applier(apply_all_present_category_overrides);
            case 14851: // rf3PresentNpc01.bin
                return make_applier(apply_all_present_overrides, "vishnal");
            case 14852: // rf3PresentNpc02.bin
                return make_applier(apply_all_present_overrides, "clorica");
            case 14853: // rf3PresentNpc03.bin
                return make_applier(apply_all_present_overrides, "volkanon");
            case 14854: // rf3PresentNpc04.bin
                return make_applier(apply_all_present_overrides, "forte");
            case 14855: // rf3PresentNpc05.bin
                return make_applier(apply_all_present_overrides, "kiel");
            case 14856: // rf3PresentNpc06.bin
                return make_applier(apply_all_present_overrides, "bado");
            case 14857: // rf3PresentNpc07.bin
                return make_applier(apply_all_present_overrides, "margaret");
            case 14858: // rf3PresentNpc08.bin
                return make_applier(apply_all_present_overrides, "dylas");
            case 14859: // rf3PresentNpc09.bin
                return make_applier(apply_all_present_overrides, "arthur");
            case 14860: // rf3PresentNpc10.bin
                return make_applier(apply_all_present_overrides, "porcoline");
            case 14861: // rf3PresentNpc11.bin
                return make_applier(apply_all_present_overrides, "xiao_pai");
            case 14862: // rf3PresentNpc12.bin
                return make_applier(apply_all_present_overrides, "lin_fa");
            case 14863: // rf3PresentNpc13.bin
                return make_applier(apply_all_present_overrides, "amber");
            case 14864: // rf3PresentNpc14.bin
                return make_applier(apply_all_present_overrides, "illuminata");
            case 14865: // rf3PresentNpc15.bin
                return make_applier(apply_all_present_overrides, "doug");
            case 14866: // rf3PresentNpc16.bin
                return make_applier(apply_all_present_overrides, "blossom");
            case 14867: // rf3PresentNpc17.bin
                return make_applier(apply_all_present_overrides, "dolce");
            case 14868: // rf3PresentNpc18.bin
                return make_applier(apply_all_present_overrides, "jones");
            case 14869: // rf3PresentNpc19.bin
                return make_applier(apply_all_present_overrides, "nancy");
            case 14870: // rf3PresentNpc20.bin
                return make_applier(apply_all_present_overrides, "leon");
            case 14871: // rf3PresentNpc21.bin
                return make_applier(apply_all_present_overrides, "ventuswill");
            case 14872: // rf3PresentNpc22.bin
                return make_applier(apply_all_present_overrides, "noel");
            case 14873: // rf3PresentNpc23.bin
                return make_applier(apply_all_present_overrides, "luna");
            case 14874: // rf3PresentNpc24.bin
                return make_applier(apply_all_present_overrides, "barrett");
            case 14875: // rf3PresentNpc25.bin
                return make_applier(apply_all_present_overrides, "raven");
            case 14876: // rf3PresentNpc26.bin
                return make_applier(apply_all_present_overrides, "mist");
            case 14877: // rf3PresentNpc27.bin
                return make_applier(apply_all_present_overrides, "traveler");
            default:
                return {};
        }
    }

    void hooked_load_asset(SafetyHookContext& ctx) {
        auto* const data = reinterpret_cast<void*>(ctx.rsi); // NOLINT(performance-no-int-to-ptr)
        if (!data) {
            return;
        }
        const auto file_index = static_cast<uint32_t>(ctx.r14 & 0xffffffff);
        const auto file_size = static_cast<uint32_t>(ctx.rbx & 0xffffffff);
        const auto apply = get_override_applier(file_index);
        if (!apply) {
            return;
        }
        // Exceptions must not propagate into the game's code, so a file that fails to apply is left unmodified.
        try {
            apply(Mods::loaded(), data, file_size);
        } catch (const std::exception& e) {
            PLOG_ERROR << "Couldn't apply overrides to file index " << file_index << ": " << e.what();
        } catch (...) {
            PLOG_ERROR << "Couldn't apply overrides to file index " << file_index << ": unknown error";
        }
    }
} // namespace

void install() {
    // RVA 0x24252f is just after the log_message call in nsFileArchiveLoadInReadFile and before the file name string
    // is destroyed.
    g_load_asset_hook = safetyhook::create_mid(Address::RVA(0x24252f), hooked_load_asset);

    PLOG_INFO << "Installed config data hook";
}

void uninstall() {
    g_load_asset_hook.reset();
}
} // namespace ConfigDataHook
