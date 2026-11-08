# Venti

Mod loader for [Rune Factory 4 Special](https://runefactory.com/rf4/) (PC).

## What & Why

The original version of Rune Factory 4 was developed for the Nintendo 3DS and is based on a completely custom game
engine built by the now-defunct Neverland. It was later ported to the Nintendo Switch by Marvelous USA, and the Switch
port was re-ported to PC using a variant of the Digital Eclipse engine by Muteki Games.

The point is: for modders interested in this game, no generic game-modding framework exists that can possibly support
it. There is no Unity or Unreal Engine behind the scenes, nor even any lesser-known niche like Gamebryo or GameMaker.
It is the wild west, and little progress has been made since the PC version was first released.

This project aims to advance the status quo, open up new possibilities and, hopefully, lead to more mods being released.
Inspired by the parallel development of [RF4S Modding Toolkit](https://github.com/arryndoestech/rf4-modkit), its goal is
to solve the "other half" of the modding problem, specifically the dirty job of patching in data at runtime and handling
dependencies and load-order conflicts instead of relying on wholesale replacement of bundled assets.

If you've modded Stardew Valley, or simply installed mods for that game, then you might know the difference between
legacy [XNB mods](https://stardewvalleywiki.com/Modding:Using_XNB_mods) and [SMAPI](https://smapi.io/). That is roughly
analogous to the difference between RF4 "bundle" mods and what is planned for Venti.

## Installation

Simply download the [latest release](https://codefloe.com/droopy_dingo/venti/releases/latest), and extract the files to
your Rune Factory 4 Special installation directory.

If you're not sure which directory this is, do the following in Steam:

- Right-click on Rune Factory 4 Special -> Properties
- Select the "Installed Files" tab on the left
- Click the "Browse" button.
- Drag files or extract to the folder that pops up.

### Technical Stuff

Venti ships as a `version.dll` proxy; this is a DLL that is loaded by the game, which--standard Windows behavior--will
load a local copy in the same directory, if found, instead of the system version. This is what allows Venti to do its
thing and patch in modded behavior. You may have used other loaders, for other games, that ship as files like
`dinput8.dll` or `dxgi.dll`; this is the exact same concept, just a different DLL.

Due to how these tools must be coded, it's possible that Windows Defender or some antivirus programs will flag the DLL
as a trojan or malware. This is a false positive. You can verify for yourself, as the library is fully open-source.
Absolutely nothing is hidden or obfuscated. Game mods sometimes cause false positives because they overwrite function
calls in a running process, which is precisely what a mod/loader must do in order to be useful.

## Current State/Features

This software is alpha, maybe even pre-alpha. It is being released early to coincide with the Modding Toolkit release,
and generate feedback and (we hope) some renewed enthusiasm for the game and its modding potential. The feature set is
very small--literally just one major feature at present--but will grow over time. Probably.

### Mod Structure

To start adding mods, create a `mods` directory in your RF4S folder, and one subdirectory for each installed mod.

Example of the directory structure:

```
Rune Factory 4 Special/
- mods/
    - My First Mod/
        - mod.toml
    - My Second Mod/
        - foo.toml
        - bar.toml
- RF4S.exe
- venti.toml
- version.dll
```

### Load Order

You do **not** need to define an explicit load order in order for mods to be loaded; however, you **may** do so if you
have multiple mods that make conflicting edits and need to control the winners and losers.

To do so, add the following section anywhere in your `venti.toml`:

```toml
[mods]
load_order = ["First Mod", "Second Mod", "Third Mod"]
```

Load order is _first to last_. In other words, the "Third Mod" above will be the _winner_ of any conflicts with either
the Second or First mods; and the Second Mod will win any conflicts with the First.

If a load order is configured, any mods in the `mods/` directory that are not specified in the load order will still be
loaded, but in an arbitrary order and after all the mods that _are_ configured.

### Data Patching

Venti supports record- and field-level patching of game data tables. Instead of replacing an entire file, such as
`rf3ItemList.bin`, with a lot of hex edits, you write a single [TOML](https://toml.io/) file that looks like this:

```toml
[item.1] # Cabbage
buy = 2000
sell = 800

[item.882] # Love Crystal
rarity = 12

[equipment.746] # Dragon Cloak
fire_res = 400
water_res = 400
```

Note how there's an `[equipment]` section alongside the `[item]` sections. These TOML files (called "override files"
here) are not limited to targeting a single `.bin` file; you can create and distribute as many TOML files as you want,
with as many records as you want in each, across as many record types and subtypes as you want. This can help to keep
your mods organized, or provide users of the mod with further customization options.

Every section is of one of these formats:

- `[type.id]` - modifies 1 record of a type that only has one table, such as `[item.1]`
- `[type.sub.id]` - modifies 1 record of a type that is spread across many tables, such as `[recipe.oven.5]`
- `[type.sub.group.id]` - modifies 1 record of a type that is spread across many tables _and_ where each table has
  multiple sections. This mainly applies to presents and present categories, e.g. `[present.margaret.likes.1]`.

There is also the `[type.sub.group]` variant of the last format, where you can specify entire records inline such as:

```toml
[present.margaret.likes]
2 = { item = 13, fp = 9 }
3 = { item = 14, fp = 15 }
```

The effect of this is exactly the same as adding records like `[present.margaret.likes.2]`, just more compact.

Full documentation for all the TOML supported fields is still in progress, but the C++ side is clearly documented, so
use the following as a guide to table/group names. Click the link on each one to see the C++ struct with details on
all the field names and their meanings:

| Type             | Sub           | Real File                    | Groups                           | Struct                                         | Explanation                                               |
|------------------|---------------|------------------------------|----------------------------------|------------------------------------------------|-----------------------------------------------------------|
| crop             |               | `rf3CropParam.bin`           |                                  | [`Crop`](src/rf/crop.h)                        | Crop growth settings                                      |
| equipment        |               | `rf3ItemEquipmentParam.bin`  |                                  | [`EquipmentParam`](src/rf/equipment_param.h)   | Weapon and gear attributes                                |
| fish_level       | (fishing)     | `Fishing_rate_fish_lv_*.bin` |                                  | [`FishLevelRate`](src/rf/fish_level_rate.h)    | Level/size buckets for fish                               |
| fish             | (fishing)     | `Fishing_rate_fish_*.bin`    |                                  | [`FishRate`](src/rf/fish_rate.h)               | Fish spawn locations and rates                            |
| geode            |               | `MapOre_Rate.bin`            |                                  | [`GeodeRate`](src/rf/geode_rate.h)             | Minable node types and yields                             |
| item             |               | `rf3ItemList.bin`            |                                  | [`Item`](src/rf/item.h)                        | Details of all obtainable items                           |
| level            |               | `rf3Parameter.bin`           |                                  | [`LevelUp`](src/rf/level_up.h)                 | Combat level requirements and target stats                |
| magic            |               | `rf3ParamMagic.bin`          |                                  | [`MagicParam`](src/rf/magic_param.h)           | Attributes of magic/rune abilities                        |
| monster_gift     |               | `rf3MonsterPresent.bin`      |                                  | [`MonsterGift`](src/rf/monster_gift.h)         | Liked gifts for tameable monsters                         |
| npc              |               | `rf3NpcParam.bin`            |                                  | [`NpcParam`](src/rf/npc_param.h)               | NPC stats, visuals, item drops, etc.                      |
| present          | (npc_name)    | `rf3PresentNpc*.bin`         | `dislikes`, `likes`, `loves`     | [`Present`](src/rf/present.h)                  | Gift preferences for the various named characters         |
| present_category |               | `rf3PresentCategory.bin`     | `trash`, `cakes`, `sweets`, etc. | [`PresentCategory`](src/rf/present_category.h) | Categories used in some gift preferences                  |
| prices           |               | `rf3PriceTable.h`            |                                  | [`PriceTable`](src/rf/price_table.h)           | Price classes with buy/sell multipliers per level         |
| recipe           | (recipe_type) | `rf3Recipe*.bin`             |                                  | [`Recipe`](src/rf/recipe.h)                    | Recipes for Accessories (Crafting)                        |
| skill_action     |               | `rf3ParamSkillData.bin`      |                                  | [`SkillDataParam`](src/rf/skill_data_param.h)  | RP cost and Skill XP gained for performing actions        |
| skill_exp        | (skill_type)  | `rf3ParamSkillExp*.bin`      |                                  | [`SkillExpParam`](src/rf/skill_exp_param.h)    | XP required, per skill level, to reach next skill level   |
| skill_stat       |               | `rf3ParamSkill.bin`          |                                  | [`SkillStat`](src/rf/skill_stat.h)             | Player stat gains received per skill level-up             |
| upgrade          |               | `rf3ItemStrengthening.bin`   |                                  | [`Upgrade`](src/rf/upgrade.h)                  | Bonuses that upgrade materials apply to equipment or food | 
| use              |               | `rf3UseItemParam.bin`        |                                  | [`ItemUseParam`](src/rf/item_use_param.h)      | Effects of items when used (i.e. eaten)                   |

Subtypes noted above include:

| Sub         | Possible Values                                                                                                                                                                                                                                                    |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fishing     | `spring`, `spring2`                                                                                                                                                                                                                                                |
| npc_name    | `amber`, `arthur`, `bado`, `barrett`, `blossom`, `clorica`, `dolce`, `doug`, `dylas`, `forte`, `illuminata`, `jones`, `kiel`, `leon`, `lin_fa`, `luna`, `margaret`, `mist`, `nancy`, `noel`, `porcoline`, `raven`, `ventuswill`, `vishnal`, `volkanon`, `xiao_pai` |
| recipe_type | `accessory`, `armor`, `axe_hammer`, `chemistry`, `dual_blade`, `fist`, `frying_pan`, `handmade`, `headgear`, `knife`, `long_sword`, `mixer`, `oven`, `pot`, `shield`, `shoes`, `short_sword`, `spear`, `staff`, `steamer`, `tool`                                  |
| skill_type  | `combat`, `field`, `lifestyle`, `synthesis`, `tools`                                                                                                                                                                                                               |

Notes:

- The `id` is always the index of the record in the file. The game does not have any true concept of an "ID".
- If multiple `Groups` are available, then all groups have the same format and semantics.

## Development/Roadmap

Many, many features still need to be added. In the very near future:

- [ ] Enum and percent values in TOML, such as `fire_res = 10%` for equipment or `flags = WinterGood | SpringGood` for a
  crop.
- [ ] Ability to mod localization data (in-game text)
- [ ] Integration of community bugfixes for crash on reload, high idle CPU, etc.
- [ ] Ability to add new records to tables (not always supported by the game itself, but works sometimes)

Not-too-distant future:

- [ ] Replace atomic assets (models, textures, etc.) with assets packaged in mods, honoring load order
- [ ] Support for patching and merging script banks and event definitions created/edited by the modkit
- [ ] Ability to disable mods without deleting/uninstalling them
- [ ] Support for loading code mods (other DLLs) that do their own patching from scratch
- [ ] Real documentation for all these features, aside from this half-baked README file

Pie in the sky features that may need help from the community:

- [ ] APIs for code mods, including:
    - [ ] Reading and writing game state such as time, actor values, event flags, etc.
    - [ ] Reading the loader config (e.g. debug settings) and information about other loaded mods
    - [ ] Graphical overlays (e.g. imgui) and modifications to the shader pipeline
    - [ ] An ever-growing list of functions addresses + signatures that can be hooked as reverse-engineering progresses
- [ ] Support for new or updated in-game UI based on the Muteki framework definitions
- [ ] Integration of map edits from the modkit

Requests are welcome, but please keep in mind that at present, virtually any request not already listed above is going
to require not only engineering work but _reverse engineering_ substantial parts of the game's implementation. This is
time-consuming and frequently frustrating, so until this project is a little more mature, personal requests are likely
to be ignored in the short term unless you are contributing some of the knowledge or implementation.

## Contributions

In a fledgling project such as this, most contributions probably aren't going to be turned down, and it as far too early
to worry about detailed guidelines and reasons for acceptance/rejection. However, a few things are important to declare
up front:

### Scope

The mod loader's responsibilities should be limited to features that are entirely transparent to the player: loading
the player's installed mods, exposing capabilities to those mods, and stability/performance patches for the game.
Please do not submit code that would visibly change the game's appearance or behavior; write your own mod instead.

### Style

This project uses clang-tidy and clang-format. Before sending a PR:

- Resolve all build warnings emitted by clang-tidy, or suppress them if there is a defensible reason for it.
- Run clang-format to format your code. This is integrated into Git; just run `git clang-format`.

### AI

This project incorporates cautious, conservative, constrained use of AI. For example, models may be used to:

- Analyze the game binary/decompilation to help locate and/or explain certain behaviors, pending manual verification
- Quickly cross-reference data from disparate sources (bundle dumps, datamining spreadsheets, tests)
- Suggest rough outlines of feature implementations or identify missing steps in an existing plan
- Perform tedious refactoring tasks such as mass renames or function parameterization
- Perform tedious testing tasks like initializing large fixtures
- Quickly look up cryptic errors and identify possible causes
- Review human-written code and identify unexplored risks and edge cases

Models are **NOT** used to:

- Implement whole features or fix bugs based on descriptions or functional specifications
- Generate documentation or communication artifacts, internal or external
- Review their own code, or code generated by another model
- Write any code that will not be subject to a full and detailed human review
- Perform direct interactions with the repo (commits, PRs, etc.) or with third parties

The above is not necessarily an exhaustive list of all dos and don'ts, it only means to clarify the difference between
_AI assistance_, which is allowed and encouraged, and _vibe coding_, which is not and will be rejected on detection.

This distinction is made in the hope of boosting productivity while still minimizing slop. If you are not comfortable
with these very modest restrictions, please reserve your code submission and create an issue instead.

## Support/Contact

If you prefer not to submit an issue or register an account here, you can reach the author on the
[SoS/RF Modding](https://discord.gg/HyFAcwN9) Discord server, in the RF 4 Special channels. Please follow normal Discord
etiquette: ask your question in chat, do not DM out of the blue, and do not repeatedly ping if you don't get an
immediate response.