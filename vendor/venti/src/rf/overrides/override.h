#pragma once

#include "../../mods/mod.h"
#include "../config_data.h"

#include "plog/Log.h"

#include <toml++/toml.hpp>

#include <array>
#include <charconv>
#include <functional>
#include <limits>
#include <optional>
#include <span>
#include <sstream>
#include <string>
#include <string_view>
#include <type_traits>
#include <vector>

namespace RFConfig {

struct OverrideContext {
    const std::string& mod_name;
    const std::string& override_file_name;
    const char* table_name;
    const char* partition_name;
    uint32_t group_index;
    std::string group_name;

    [[nodiscard]] std::string full_table_name(const std::optional<uint32_t> id = std::nullopt) const {
        std::stringstream ss;
        ss << "[" << table_name;
        if (partition_name && partition_name[0]) {
            ss << "." << partition_name;
        }
        if (id.has_value()) {
            ss << "." << id.value();
        }
        ss << "]";
        return ss.str();
    }
};

template <typename T>
void apply_overrides(ConfigFile<T>& config, const toml::table* override_table,
                     const std::function<void(const toml::table& tbl, T& record)>& apply_override,
                     const OverrideContext& ctx) {
    override_table->for_each([&](const toml::key& key, auto&& val) {
        const auto sv = key.str();
        uint32_t id;
        auto result = std::from_chars(sv.data(), sv.data() + sv.size(), id);
        if (result.ec != std::errc{} || result.ptr != sv.data() + sv.size()) {
            PLOG_ERROR.printf("Invalid ID '%s' specified for table '%s'. (Mod: %s, File: %s)", key.data(),
                              ctx.full_table_name().c_str(), ctx.mod_name.c_str(), ctx.override_file_name.c_str());
            return;
        }
        if (!toml::is_table<decltype(val)>) {
            PLOG_ERROR.printf("Entry [%s.%u] is not a table. (Mod: %s, File: %s)", ctx.full_table_name().c_str(), id,
                              ctx.mod_name.c_str(), ctx.override_file_name.c_str());
            return;
        }
        if (id >= config.count(ctx.group_index)) {
            PLOG_ERROR.printf(
                "Out-of-range ID %u (max: %u) specified for group '%s' in table '%s'. (Mod: %s, File: %s)", id,
                config.count(ctx.group_index) - 1, ctx.group_name.c_str(), ctx.full_table_name().c_str(),
                ctx.mod_name.c_str(), ctx.override_file_name.c_str());
            return;
        }
        apply_override(*val.as_table(), config.get(id, ctx.group_index));
    });
}

// Searches all loaded mods for overrides to a given record type `T` and applies all overrides found.
template <typename T>
void apply_all_overrides(ConfigFile<T>& config,
                         const std::function<void(const toml::table& tbl, T& record)>& apply_override,
                         const std::vector<Mods::LoadedMod>& mods, const char* table_name,
                         const char* partition_name = "", std::span<const std::string_view> group_names = {}) {
    for (const auto& mod : mods) {
        for (const auto& override_file : mod.override_files) {
            const auto& tbl = override_file.table;
            if (!tbl.contains(table_name)) {
                continue;
            }
            auto table_node = tbl[table_name];
            if (!table_node.is_table()) {
                PLOG_ERROR.printf("Entry '%s' is not a table. (Mod: %s, File: %s)", table_name, mod.name.c_str(),
                                  override_file.name.c_str());
                continue;
            }
            const toml::table* override_table = table_node.as_table();
            if (partition_name && partition_name[0]) {
                if (!override_table->contains(partition_name)) {
                    continue;
                }
                const auto* partition_table = override_table->get(partition_name);
                if (!partition_table->is_table()) {
                    PLOG_ERROR.printf("Entry [%s.%s] is not a table. (Mod: %s, File: %s)", table_name, partition_name,
                                      mod.name.c_str(), override_file.name.c_str());
                    continue;
                }
                override_table = partition_table->as_table();
            }
            OverrideContext ctx{
                .mod_name = mod.name,
                .override_file_name = override_file.name,
                .table_name = table_name,
                .partition_name = partition_name,
            };
            if (group_names.empty()) {
                apply_overrides(config, override_table, apply_override, ctx);
            } else {
                for (uint32_t group_index = 0; group_index < group_names.size(); group_index++) {
                    const std::string_view group_name = group_names[group_index];
                    if (!override_table->contains(group_name)) {
                        continue;
                    }
                    const auto* const group_table = override_table->get(group_name);
                    if (!group_table->is_table()) {
                        PLOG_ERROR.printf("Entry [%s.%s] is not a table. (Mod: %s, File: %s)",
                                          ctx.full_table_name().c_str(), std::string(group_name).c_str(),
                                          mod.name.c_str(), override_file.name.c_str());
                        continue;
                    }
                    ctx.group_index = group_index;
                    ctx.group_name = group_name;
                    apply_overrides(config, group_table->as_table(), apply_override, ctx);
                }
            }
        }
    }
}

// Formats a TOML node for log messages: scalars as their TOML value, tables and arrays as their type name.
inline std::string describe_toml_node(const toml::node& node) {
    std::ostringstream ss;
    if (node.is_table() || node.is_array()) {
        ss << node.type();
    } else {
        node.visit([&](auto&& n) { ss << n; });
    }
    return ss.str();
}

// Converts `node` to the integer type `T`. Logs a warning and returns `std::nullopt` if the node is not an integer, or
// is outside the range `min` to `max`, which defaults to the full range of `T`.
template <typename T>
std::optional<T> read_override_integer(const toml::node& node, std::string_view key,
                                       // NOLINTNEXTLINE(bugprone-signed-char-misuse): int8_t min is meant to be -128.
                                       int64_t min = std::numeric_limits<T>::min(),
                                       int64_t max = std::numeric_limits<T>::max()) {
    static_assert(std::is_integral_v<T> && sizeof(T) <= sizeof(int32_t), "Unsupported override field type");
    auto value = node.value_exact<int64_t>();
    if (!value) {
        PLOG_WARNING << "Override '" << key << "' must be an integer from " << min << " to " << max << ", but found "
                     << describe_toml_node(node) << "; ignoring.";
        return std::nullopt;
    }
    if (*value < min || *value > max) {
        PLOG_WARNING << "Override '" << key << "' must be from " << min << " to " << max << ", but found " << *value
                     << "; ignoring.";
        return std::nullopt;
    }
    return static_cast<T>(*value);
}

// Converts `node` to the field type `T`, which may be an integer or an enum with an integer underlying type. Logs a
// warning and returns `std::nullopt` if the value is the wrong type or out of range.
template <typename T>
std::optional<T> read_override_value(const toml::node& node, std::string_view key) {
    if constexpr (std::is_enum_v<T>) {
        if (auto value = read_override_integer<std::underlying_type_t<T>>(node, key)) {
            return static_cast<T>(*value);
        }
        return std::nullopt;
    } else {
        return read_override_integer<T>(node, key);
    }
}

// Calls `set` with the value of `key` in `tbl`, if present, for fields packed into 4 bits. Missing keys are ignored;
// values that are the wrong type or outside 0-15 are ignored with a warning.
template <typename Set>
void read_nibble_override(const toml::table& tbl, const std::string_view key, Set set) {
    if (const auto* node = tbl.get(key)) {
        if (auto value = read_override_integer<uint8_t>(*node, key, 0, 0x0F)) {
            set(*value);
        }
    }
}

// Replaces `field` with the value of `key` in `tbl`, if present. Missing keys leave the field unchanged; values that
// are the wrong type or out of range for the field also leave it unchanged, with a warning.
template <typename T>
void read_override(const toml::table& tbl, const std::string_view key, T& field) {
    if (const auto* node = tbl.get(key)) {
        if (auto value = read_override_value<T>(*node, key)) {
            field = *value;
        }
    }
}

// Replaces elements of `field` with the elements of the array `key` in `tbl`, starting from the first element.
// Elements past the end of the TOML array are left unchanged. Elements past the end of `field`, and elements that are
// the wrong type or out of range, are ignored with a warning.
template <typename T, size_t N>
void read_override(const toml::table& tbl, std::string_view key, std::array<T, N>& field) {
    const auto* node = tbl.get(key);
    if (!node) {
        return;
    }
    const auto* array = node->as_array();
    if (!array) {
        PLOG_WARNING << "Override '" << key << "' must be an array of up to " << N << " elements, but found "
                     << describe_toml_node(*node) << "; ignoring.";
        return;
    }
    if (array->size() > N) {
        PLOG_WARNING << "Override '" << key << "' has " << array->size() << " elements, but only " << N
                     << " are allowed; ignoring the rest.";
    }
    for (size_t i = 0; i < N && i < array->size(); i++) {
        const std::string element_key = std::string(key) + "[" + std::to_string(i) + "]";
        if (auto value = read_override_value<T>(*array->get(i), element_key)) {
            field[i] = *value;
        }
    }
}

} // namespace RFConfig
