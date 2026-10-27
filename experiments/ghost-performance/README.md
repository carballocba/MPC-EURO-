# GHOST Performance — final integration

The existing buffer and public 148-parameter contract are preserved. Performance now shares the C1 routing stage and eight Motion sources, driven by its single Ghost clock. Random remains per configured destination; Motion uses its existing global enable and routes. No second buffer, clock or public parameter was added.

New instances use the private PEF1 version2 policy. Version1 and older chunks retain historical behavior. Explicit PERFORMANCE OFF → ON opts a historical state into the new policy; new states cannot be read by old binaries. Keep trial projects separate and retain backups. Evolution zero with routing off matches previous Performance audio; 16 factory programs retain COMPAT behavior.

The GUI layout, parameter IDs, Screen/Program maps and native tabs stay fixed. The PLAY labels now identify Random target and Motion routes because they operate in new RUN states as well as COMPAT.

Build and verify from this checkout with the existing build/venv Python runtime:

```sh
build/venv/bin/python experiments/ghost-performance/build_engine.py
build/venv/bin/python experiments/ghost-performance/build_engine.py --arm
build/venv/bin/python experiments/ghost-performance/build_gui.py
build/venv/bin/python experiments/ghost-performance/inspect_gui.py
build/venv/bin/python -m unittest discover -s tests -p 'test_ghost_performance*.py' -v
build/venv/bin/python -m unittest discover -s tests -p test_ghost_final_integration.py -v
build/venv/bin/python experiments/ghost-performance/check_policy.py
build/venv/bin/python experiments/ghost-performance/validate_rt.py
build/venv/bin/python experiments/ghost-performance/final_audio.py
build/venv/bin/python experiments/ghost-performance/benchmark.py
build/venv/bin/python experiments/ghost-performance/package.py
build/venv/bin/python experiments/ghost-performance/verify_package.py
build/venv/bin/python experiments/ghost-performance/prepare_trial.py
build/venv/bin/python experiments/ghost-performance/reproduce.py
```

Run benchmark alone; retain all paired CPU/wall samples and earlier failures/outliers. Native measurements do not establish ARM deadlines. ARM is cross-compiled Cortex-A9 hardfloat against glibc2.31 maximum; no QEMU is installed. Tools used: Python3.13, clang, Pillow12.3, pyelftools0.32 and Zig0.13 in the local venv. No package/network installation is performed.

The source archive includes baseline packages, native oracle and generated includes, not personal MPC.settings snapshots or user music. Transaction tests now use synthetic settings with79 entries and preserve its bytes/inode. The data profile over the existing transaction refers to the LAST VERIFIED installed Performance321 package, not Buffer Engine338. It fails closed if a future device read differs. No preflight, install, service operation or SSH is run by this work.

The single final development report is docs/ghost/GHOST_FINAL_DEVELOPMENT_REPORT.md.
