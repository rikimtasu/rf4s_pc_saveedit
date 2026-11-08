#pragma once

#include <cstdint>

namespace RFConfig {

// Cooking, chemistry, crafting and forging recipes.
//
// Each cooking utensil, chemistry and equipment type has its own file, all sharing this layout. Record 0 of each file
// is blank. Crafting and forging recipes never use `material_6`.
//
// Files:
// - rf3RecipeAcce.bin (Accessories)
// - rf3RecipeArmor.bin (Armor)
// - rf3RecipeCookFry.bin (Frying Pan)
// - rf3RecipeCookHandmade.bin (Handmade)
// - rf3RecipeCookKnife.bin (Knife)
// - rf3RecipeCookMixer.bin (Mixer)
// - rf3RecipeCookOven.bin (Oven)
// - rf3RecipeCookPan.bin (Pot)
// - rf3RecipeCookSteamer.bin (Steamer)
// - rf3RecipeDrug.bin (Chemistry)
// - rf3RecipeFarm.bin (Farm Tool)
// - rf3RecipeHat.bin (Headgear)
// - rf3RecipeShield.bin (Shield)
// - rf3RecipeShoes.bin (Shoes)
// - rf3RecipeWeaponA.bin (Short Sword)
// - rf3RecipeWeaponB.bin (Long Sword)
// - rf3RecipeWeaponC.bin (Spear)
// - rf3RecipeWeaponD.bin (Axe/Hammer)
// - rf3RecipeWeaponE.bin (Unknown)
// - rf3RecipeWeaponK.bin (Staff)
// - rf3RecipeWeaponM.bin (Dual Blade)
// - rf3RecipeWeaponN.bin (Fist)
struct Recipe {
    // ID of the item produced by this recipe.
    uint16_t result;

    // Item ID for the first ingredient (required).
    uint16_t material_1;

    // Item ID for the second ingredient (optional).
    uint16_t material_2;

    // Item ID for the third ingredient (optional).
    uint16_t material_3;

    // Item ID for the fourth ingredient (optional).
    uint16_t material_4;

    // Item ID for the fifth ingredient (optional).
    uint16_t material_5;

    // Item ID for the sixth ingredient (optional).
    uint16_t material_6;

    // "Recommended" level to make. Players at lower level will have to expend much more RP to make the recipe, but will
    // gain much more skill XP.
    uint16_t level;

    // Which flag (bit) is used in the game to indicate that the player has learned this recipe.
    // Must be unique across ALL recipes, not just per category/file.
    uint32_t learned_flag_id;
};

static_assert(sizeof(Recipe) == 0x14);
} // namespace RFConfig
