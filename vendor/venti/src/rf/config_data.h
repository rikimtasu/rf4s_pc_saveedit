#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace RFConfig {

// Binary header for game configuration (e.g. NLCL) files. Follows a fixed structure.
struct Header {
    // File type, usually "NLCL" for most files of interest.
    std::array<char, 4> type_name;

    // Has strong correlation to the `type_name`, but exact meaning is not fully understood.
    // Tends to be the value 0x20201123 in RF4 (was different in RF3).
    uint32_t type_id;

    // Usually zeroed in NLCL files, but can be defined for other file types, and its meaning is unknown.
    uint32_t unknown1;

    // Usually zeroed in NLCL files and may be part of a 64-bit value with `unknown1`. Currently specified as a
    // separate field to prevent struct padding.
    uint32_t unknown2;

    // Number of record groups in the file, including the root group that immediately follows the header. Most files
    // have only the root group. In files with more than one, the root's records hold the file offsets of the other
    // groups.
    uint32_t group_count;

    // The byte offset of the group table relative to the beginning of the file, NOT from the current read position.
    // The table has one `GroupTableEntry` per group, followed by the lists of reference positions.
    uint32_t group_table_position;

    // Number of records in the root group. Each group, including the root, begins with a count like this one, followed
    // by that many fixed-size records.
    uint32_t entry_count;
};

// Entry in the group table (formerly considered the "footer") of a game configuration file.
struct GroupTableEntry {
    // Always 0 in every file checked so far.
    uint32_t unknown;

    // The byte offset of the group's record count relative to the beginning of the file. For the root group, this is
    // the position of `Header::entry_count`.
    uint32_t position;

    // Number of fields elsewhere in the file that hold this group's `position`. Always 0 for the root group.
    uint32_t reference_count;

    // The byte offset of a list of `reference_count` 32-bit values, each being the position of a field holding this
    // group's `position`.
    uint32_t references_position;
};

// Interface for a game configuration file/asset, overlaying the memory region where the asset data is loaded.
template <typename T>
class ConfigFile {
private:
    static_assert(std::is_trivially_copyable_v<T>, "Record types must be plain structs");

    char* data;
    size_t size;
    bool raw;

    ConfigFile(char* data, size_t size, bool raw);

    [[nodiscard]] const Header& header() const;

    // Gets the byte offset of a group's record count, after checking that the group exists.
    [[nodiscard]] size_t group_position(uint32_t group) const;

public:
    // Initializes a `ConfigFile` instance as an overlay of a loaded asset's binary data.
    //
    // `size` is the length of the data in bytes. If `raw` is true, the data has no header and consists entirely of
    // records, so the record count is determined by the size.
    static ConfigFile overlay(void* data, size_t size, bool raw = false);

    // Gets the number of record groups in the file.
    //
    // In files with more than one group, the root group only holds the positions of the other groups, so it is not
    // counted and cannot be accessed; group 0 is the first group after the root. Otherwise, group 0 is the root.
    [[nodiscard]] uint32_t group_count() const;

    // Gets the number of records in a group.
    [[nodiscard]] uint32_t count(uint32_t group = 0) const;

    // Gets a reference to the record at a specified position within a group.
    T& get(uint32_t index, uint32_t group = 0);
};
} // namespace RFConfig
