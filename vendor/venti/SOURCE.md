# Venti reference

Repository: https://codefloe.com/droopy_dingo/venti

Pinned commit: `6588b5ff7c28ddd82fd5b2a4591486af3e9c901a`

These unmodified source references were retrieved through Codefloe’s public contents API. The loader itself is not built, bundled or installed. Its GNU GPL v3 license is retained in `LICENSE` and the workspace’s `COPYING`.

`scripts/build_game_schema.py` derives field names from actual `read_override` / `read_nibble_override` handlers, types and offsets from the C++ structs, and filenames / partitions / raw-table selection from `src/hooks/config_data_hook.cpp`. Generated record sizes must match every upstream `static_assert(sizeof(...))`.

The metadata contains 19 table definitions, 400 named fields and 72 file variants. The save editor uses four item-related tables as read-only references. The hook source determines filenames; the reference reader validates NLCL bounds and record widths. These are asset definitions, not save-offset mappings.

The reference reader and derived schema are distributed under GPL-3.0; see `COPYING`. Existing MIT save-format references retain their notices. No mod builder, TOML parser, ZIP exporter, loader or runtime mod feature is included.
