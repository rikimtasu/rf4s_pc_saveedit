#include "config_data.h"

#include "crop.h"
#include "equipment_param.h"
#include "fish_level_rate.h"
#include "fish_rate.h"
#include "geode_rate.h"
#include "item.h"
#include "item_use_param.h"
#include "level_up.h"
#include "magic_param.h"
#include "monster_gift.h"
#include "npc_param.h"
#include "present.h"
#include "present_category.h"
#include "price_table.h"
#include "recipe.h"
#include "skill_data_param.h"
#include "skill_exp_param.h"
#include "skill_stat.h"
#include "upgrade.h"

#include <cstddef>
#include <cstdint>
#include <format>
#include <stdexcept>

namespace RFConfig {

template <typename T>
ConfigFile<T>::ConfigFile(char* data, size_t size, bool raw) : data(data), size(size), raw(raw) {}

template <typename T>
ConfigFile<T> ConfigFile<T>::overlay(void* data, size_t size, bool raw) {
    auto* bytes = static_cast<char*>(data);
    if (raw) {
        if (size % sizeof(T) != 0) {
            throw std::invalid_argument(
                std::format("Invalid data size: {} is not a multiple of record size {}", size, sizeof(T)));
        }
        return ConfigFile(bytes, size, true);
    }
    if (size < sizeof(Header)) {
        throw std::invalid_argument(
            std::format("Invalid data size: {} is smaller than the header size {}", size, sizeof(Header)));
    }
    const auto* h = reinterpret_cast<const Header*>(bytes);
    if (h->group_count == 0) {
        throw std::invalid_argument("Invalid group count: 0");
    }
    if (h->group_count == 1) {
        size_t expected_table_position = sizeof(Header) + (sizeof(T) * h->entry_count);
        if (h->group_table_position != expected_table_position) {
            throw std::invalid_argument(std::format(
                "Invalid group table position: expected {} based on entry count {} and record size {}, got {}",
                expected_table_position, h->entry_count, sizeof(T), h->group_table_position));
        }
        if (h->group_table_position > size) {
            throw std::invalid_argument(
                std::format("Invalid group table position: {} is past the end of the data ({} bytes)",
                            h->group_table_position, size));
        }
        return ConfigFile(bytes, size, false);
    }
    const size_t table_end = h->group_table_position + (sizeof(GroupTableEntry) * h->group_count);
    if (table_end > size) {
        throw std::invalid_argument(
            std::format("Invalid group table: {} groups at position {} extend past the end of the data ({} bytes)",
                        h->group_count, h->group_table_position, size));
    }
    // The root group's records may differ in size from `T`, so only the groups after it are checked.
    const auto* table = reinterpret_cast<const GroupTableEntry*>(bytes + h->group_table_position);
    for (uint32_t i = 1; i < h->group_count; i++) {
        size_t position = table[i].position;
        size_t end = i + 1 < h->group_count ? table[i + 1].position : h->group_table_position;
        if (position < sizeof(Header) || position + sizeof(uint32_t) > end) {
            throw std::invalid_argument(
                std::format("Invalid group {} position: {} is outside the record data ({} to {})", i - 1, position,
                            sizeof(Header), end));
        }
        uint32_t group_entry_count = *reinterpret_cast<const uint32_t*>(bytes + position);
        size_t expected_end = position + sizeof(uint32_t) + (sizeof(T) * group_entry_count);
        if (expected_end != end) {
            throw std::invalid_argument(std::format(
                "Invalid group {}: expected to end at {} based on entry count {} and record size {}, got {}", i - 1,
                expected_end, group_entry_count, sizeof(T), end));
        }
    }
    return ConfigFile(bytes, size, false);
}

template <typename T>
const Header& ConfigFile<T>::header() const {
    return *reinterpret_cast<const Header*>(data);
}

template <typename T>
size_t ConfigFile<T>::group_position(uint32_t group) const {
    if (group >= group_count()) {
        throw std::out_of_range(std::format("Group {} out of range for {} groups", group, group_count()));
    }
    if (header().group_count == 1) {
        return offsetof(Header, entry_count);
    }
    const auto* table = reinterpret_cast<const GroupTableEntry*>(data + header().group_table_position);
    return table[group + 1].position;
}

template <typename T>
uint32_t ConfigFile<T>::group_count() const {
    if (raw || header().group_count == 1) {
        return 1;
    }
    return header().group_count - 1;
}

template <typename T>
uint32_t ConfigFile<T>::count(uint32_t group) const {
    if (raw) {
        if (group != 0) {
            throw std::out_of_range(std::format("Group {} out of range for 1-group raw file", group));
        }
        return static_cast<uint32_t>(size / sizeof(T));
    }
    return *reinterpret_cast<const uint32_t*>(data + group_position(group));
}

template <typename T>
T& ConfigFile<T>::get(uint32_t index, uint32_t group) {
    uint32_t group_entry_count = count(group);
    if (!raw && index >= group_entry_count) {
        throw std::out_of_range(
            std::format("Index {} out of range for {} records in group {}", index, group_entry_count, group));
    }
    const size_t start = raw ? 0 : group_position(group) + sizeof(uint32_t);
    size_t offset = start + (static_cast<size_t>(index) * sizeof(T));
    if (offset + sizeof(T) > size) {
        throw std::out_of_range(
            std::format("Record {} at offset {} extends past the end of the data ({} bytes)", index, offset, size));
    }
    return *reinterpret_cast<T*>(data + offset);
}

template class ConfigFile<Crop>;
template class ConfigFile<EquipmentParam>;
template class ConfigFile<FishLevelRate>;
template class ConfigFile<FishRate>;
template class ConfigFile<GeodeRate>;
template class ConfigFile<Item>;
template class ConfigFile<ItemUseParam>;
template class ConfigFile<LevelUp>;
template class ConfigFile<MagicParam>;
template class ConfigFile<MonsterGift>;
template class ConfigFile<NpcParam>;
template class ConfigFile<Present>;
template class ConfigFile<PresentCategory>;
template class ConfigFile<PriceTable>;
template class ConfigFile<Recipe>;
template class ConfigFile<SkillDataParam>;
template class ConfigFile<SkillExpParam>;
template class ConfigFile<SkillStat>;
template class ConfigFile<Upgrade>;
} // namespace RFConfig
