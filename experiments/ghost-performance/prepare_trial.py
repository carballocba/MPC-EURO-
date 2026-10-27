#!/usr/bin/env python3
"""Prepare checksummed local data profile. No SSH/preflight/service changes."""
import hashlib,json
from generate import ROOT,OUT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rc=json.loads((OUT/'release-candidate.json').read_text())
d=dict(candidate='GHOST Performance Edition',package_sha256=sha(OUT/'ghost-performance-edition-armv7-TRIAL.zip'),binary_sha256=rc['binary_sha256'],transaction_sha256=sha(ROOT/'tools/ghost-product-transaction.sh'),runner_sha256=sha(ROOT/'tools/ghost_performance_trial.py'),shared_runner_sha256=sha(ROOT/'tools/ghost_product.py'),memory_helper_sha256=sha(ROOT/'tools/ghost_buffer_trial.py'),fallback_sha256=sha(ROOT/'build/ghost-final-installed-reference/installed-performance.zip'),settings_reference_sha256='7298d10da787c9e37b8bf98254883cd635e936d10c11f65190fd13c9b74ec21c',settings_reference_status='Historical authorized baseline only. No current device read; changed settings must fail closed for review.',fallback_files=321,fallback_binary_sha256='fb985afa7e5c1ff5fc3a4468c088ddffdf00a15aed05463809cafc925055eef5',device_access=False)
(OUT/'delivery.json').write_text(json.dumps(d,indent=2)+'\n');print('Prepared local trial data only; no connection or deployment')
