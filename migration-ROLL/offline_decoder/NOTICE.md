# Source attribution and license

`opcode_table.json` is a mechanical transcription of `MC5LIB_SYMTAB.cs` from
[DotNetSiemensPLCToolBoxLibrary](https://github.com/dotnetprojects/DotNetSiemensPLCToolBoxLibrary),
commit `3d3eea50d9b24b53481809585f73e67f93ddb1d9`.
The original relevant files are retained without modifications in `reference/`:

- `LibNoDaveConnectionLibrary/PLCs/S5/MC5/MC5LIB_SYMTAB.cs`
- `LibNoDaveConnectionLibrary/PLCs/S5/MC5/MC5toAWL.cs`

The project's GNU Lesser General Public License version 2.1 is reproduced in
`LICENSE-LGPL-2.1.txt`. This local Python derivative (`decode_mc5.py`,
`test_decoder.py`) and the adapted table are supplied under LGPL-2.1. Existing
upstream notices and license text have been preserved. Generated listings contain
user-supplied PLC program information; this notice identifies the decoding
software and does not assign a new license to the user's machine program.

Adaptation prepared 2026-10-09. It uses the source's instruction table,
ordered masks, block-header layout, six-byte formal declarations and FB-call
skip descriptors. It changes argument/immediate byte handling, makes all byte
spans explicit, reports unsupported assembler bodies, preserves raw bytes,
checks relative targets, and emits cross-references. It is an exploratory
reader rather than an official STEP 5 decoder or a converter to S7.

Known upstream issues are documented in `README.md`. The local decoder corrects
the operand label for opcode `7805` from `DX` to `DB`, using the user's native
STEP 5 V7.x listing `FB105RLS.INI` (SHA256
`947e446a3f2937a85925e4a39cff7caf6256722626bc8b90989aec81008eb81c`).
All nine occurrences in FB105 print as English `G DB` (German `E DB`), with
matching operand numbers and byte offsets. The original upstream table and C#
files remain unchanged; generated cross-references retain the upstream label
separately. See `../native_verification/FB105-comparison.json`. This focused
label correction does not establish complete PLC instruction semantics or
machine behavior.
