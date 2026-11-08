# Upstream reference

Repository: https://github.com/arryndoestech/rf4-modkit

Pinned commit: `799828a433d0e5be537b977918d5a7c773ad1200`

The unmodified `save.py`, `emflags.py` and `flagstate.py` are retained as format references and for parity checks. They are not imported by the browser editor or local server. Their MIT license is retained in `LICENSE`.

The JavaScript adaptation adds strict PC file-size checks, calendar validation, symbol bounds / overlap validation, protected checksum bytes, immutable export, and transaction history. It follows the save-specific GameFlags mapping rather than the contradictory older warning in the `emflags.py` module introduction. See the editor help for that caveat.
