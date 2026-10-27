# GHOST2.4.2 reproducible source

Canonical editable inputs are the exact `build/ghost-performance-edition/source/` C units, supporting headers/source, and `resources/` native JSON/PNG/FXP. These are shipped directly, not obtained from the owner's MPC or private historical trial archives. Development generators are retained as references; do not run them instead of the supported commands.

1. Obtain Zig0.13.0 using the pinned tools/zig-requirements.txt or its public upstream source release. Set ZIG to that executable.
2. Run `python3 rebuild.py`. Expected DSP SHA256:588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd.
3. Run `python3 package.py --out dist`. It uses Python standard-library packaging, exact resources and generic installer source. No network, private checkout or firmware is needed.
4. Optional provenance check: `python3 regenerate_knob.py` requires a local C compiler and Pillow. It creates scratch outputs and verifies byte equality with the source resource, never edits the skin.

resources/ and source modifications are permitted under their retained licenses. Rebuild checks pin the reviewed binary for release preparation; if intentionally modifying the program, adjust the expected release hash and identifiers only with a reviewed compatibility plan. Binary hash checking is a packaging safeguard, not a license restriction.

The original checkout was dirty at4b214d1622686355027cf9df90542c7a0234bb66; that commit alone is NOT this exact source. The delivered source FILES.sha256 is authoritative. No public source commit, tag or release has been created by this preparation.

Optional: python3 regenerate_mascot.py verifies all eight original project-authored sprite states byte-for-byte from their drawing function, without private build artifacts.
