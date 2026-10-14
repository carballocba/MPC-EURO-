#!/usr/bin/env python3
"""One append-only parameter registry for both VST and skin."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = json.loads((root / 'ui/params.json').read_text())
out = root / 'build'
out.mkdir(exist_ok=True)
assert len({v['key'] for v in p}) == len(p)
rows = []
for v in p:
    opts = list(v.get('options', [])) + [''] * (5-len(v.get('options', [])))
    strings = ','.join(json.dumps(x) for x in opts)
    rows.append('{%s,%s,%s,%sf,%sf,%sf,%d,%d,%d,{%s}}' % (
        json.dumps(v['key']), json.dumps(v['name']), json.dumps(v.get('unit','')),
        float(v['min']),float(v['max']),float((v['default']-v['min'])/(v['max']-v['min'])),
        len(v.get('options',[])),bool(v.get('saved')),bool(v.get('readonly')),strings))
text = '#pragma once\n#define NPARAMS %d\n' % len(p)
text += 'typedef struct { const char *key,*name,*unit; float min,max,def; int nopts,saved,readonly; const char *opts[5]; } Param;\n'
text += 'static const Param PARAMS[NPARAMS] = {\n'+',\n'.join(rows)+'\n};\n'
(out/'params.h').write_text(text)
