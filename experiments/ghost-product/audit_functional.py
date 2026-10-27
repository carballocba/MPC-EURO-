#!/usr/bin/env python3
"""Exact exported graph audit. Does not reproduce closed-source Hakai dispatch."""
import argparse,csv,json,pathlib,sys
from PIL import Image
from build import ROOT,FOLDER,TOGGLES,COMMANDS,READONLY,sha
from inspect_gui import param,intersects,exclusives
ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=ROOT/'build/ghost-functional-final');args=ap.parse_args();out=args.out
skin=out/'package'/FOLDER/'Plugin Skins';page=json.loads((skin/'TUI.json').read_text())['pageData'];defs={d['key']:d['value'] for d in page['componentDefinitions']['localComponentDefinitions']}
params=json.loads((out/'parameters.json').read_text());matrix=json.loads((out/'function-matrix.json').read_text());by={r['parameter']:r for r in matrix}
dependencies={3:'Output gain affects dry and wet; intentional gain can exceed unity',18:'Legacy cycle probability; active Repeat required; distinct from Ghost Chance 77',19:'Bend instability density; active Repeat and absolute Bend > 6 semitones required; distinct from Ghost Density 76',20:'Scene mutation requires Scene Run and scene transitions',24:'Quantized capture/region commits require active Repeat and a boundary',25:'Length grid/free mode; selected tempo affects grid lengths',26:'Length division; Length clock GRID enabled',27:'Gate MIDI trigger/hold mode; MIDI enabled, matching channel and Gate note',28:'Drive processes wet branch; active audible Repeat required',29:'Mix smoothing changes transition time, not steady-state audio',30:'Matching enabled MIDI input channel required',31:'Enable permits MIDI note/CC routing',32:'Host time valid for host sync; otherwise internal tempo fallback',33:'Internal tempo audible with host sync OFF and beat/grid-based operations',34:'Original engine random seed: cycle chance, Bend instability and scenes',35:'Random Scene selection requires Scene Run and clock/scene changes',36:'Store current controls into selected scene',37:'Selected scene probability, Scene Run enabled',38:'Selected scene duration, Scene Run enabled',39:'Selected scene enable, Scene Run enabled',46:'Freeze MIDI mode requires enabled matching-channel Freeze note',47:'Apply selected scene to base targets',48:'Legacy compatibility: modern Ghost/Motion and buffer manipulation require Legacy OFF',71:'Selected Motion source lower bound, linked to upper bound; Motion + route to hear',72:'Selected Motion source upper bound, linked to lower bound; Motion + route to hear',73:'Selected source beat/free clock; host/internal tempo determines beats',74:'Selected source Hold pauses its movement; Motion + route to hear',75:'Shared Ghost/Motion deterministic event seed; enabled engine and opportunities required',105:'Selects the source assigned to the selected Motion destination'}
for p,condition in dependencies.items():by[p]['condition']=condition
rows=[];widgets=[];errors=[];qrows=[]
q=json.loads((skin/'Q-Links.json').read_text())
for ti,tab in enumerate(page['tabs']):
 view=tab['componentName']
 for i,c in enumerate(defs[view]['componentsData']):
  p=param(c);kind=c['componentData']['type'];bounds=list(map(int,c['bounds']['bounds'].split()));conditions=c['bounds'].get('additionalInvalidatingHandles',[])
  widget={'id':f'{view}/{i}/{kind}','view':view,'name':c['componentData']['name'],'type':kind,'bounds':bounds,'visibility':conditions,'parameter':p,'host_owned':kind in defs,'focus':c['bounds']['acceptsHWFocus']=='Yes'};widgets.append(widget)
  if p is None or kind not in defs:continue
  definition=defs[kind];leaves=[]
  for j,child in enumerate(definition['componentsData']):
   leaf=child['componentData'];t=leaf['type'];x,y,w,h=map(int,child['bounds']['bounds'].split());cx,cy,cw,ch=bounds
   if not (0<=x and 0<=y and x+w<=cw and y+h<=ch):errors.append({'widget':widget['id'],'child':j,'error':'child outside control'})
   if t not in ('Button','Knob'):continue
   actions=definition['actions'];data=leaf['data'];gesture='absolute selection' if t=='Button' and data['numButtonsInGroup']>1 else 'command trigger' if p in COMMANDS else 'normalized knob drag / host overlay'
   hit=[cx+x,cy+y,w,h]
   row={**widget,'id':widget['id']+'/hit'+str(j),'hitbox':hit,'touch_event':'native Button Instant' if t=='Button' else 'native Knob vertical drag','parent_actions':actions,'gesture':gesture,'selection_value':data['buttonId']/(data['numButtonsInGroup']-1) if t=='Button' and data['numButtonsInGroup']>1 else None,'callback':'host -> AEffect.setParameter -> receive/sync_manual -> engine_control','parameter_name':by[p]['name'],'state':by[p]['state_path'],'dependency':by[p]['condition'],'visual':'Button selected image from same Data handle' if t=='Button' else 'FilmStrip/Value from same Data handle','persistence':by[p]['preset'],'automated_test':'test_ghost_functional_audit + test_ghost_product + C1 core tests','validation':'native contract + real VST/DSP offline; actual Hakai event delivery PENDING'}
   rows.append(row);leaves.append(hit)
  if not leaves:errors.append({'widget':widget['id'],'error':'declared interactive without primitive'})
 for j,p in enumerate([q['Screen Mode Q-Links']['map'][ti]['Q-Links'][f'Q-Link {x}'] for x in (13,9,5,1)]):
  owners=[x for x in widgets if x['view']==view and x['focus'] and x['parameter']==p]
  if len(owners)!=1:errors.append({'view':view,'parameter':p,'error':'focus ownership'})
  else:qrows.append({'view':view,'qlink':(13,9,5,1)[j],'parameter':p,'label':by[p]['name'],'plugin_rect':owners[0]['bounds'],'host_y_offset_assumed':86,'yellow_highlight':'PENDING PHYSICAL VALIDATION','dependency':by[p]['condition']})
for i,a in enumerate(rows):
 for b in rows[i+1:]:
  if a['view']==b['view'] and not exclusives(a['visibility'],b['visibility']) and intersects(a['hitbox'],b['hitbox']):errors.append({'a':a['id'],'b':b['id'],'error':'touch overlap'})
assert len({r['id'] for r in rows})==len(rows)
report={'views':len(page['tabs']),'widgets':len(widgets),'touch_regions':len(rows),'unique_interactive_parameters':len({r['parameter'] for r in rows}),'errors':errors,'host_dispatch':'Closed-source; not executed offline. Primitive contract derived from hardware-tested PLAY Gate.','rows':rows,'indicators_and_navigation':widgets}
# Exact source traces, rather than treating every control as just a named knob.
keys=[x.strip() for x in (ROOT/'experiments/ghost-c1/c1.h').read_text().split('enum { P_GHOST,',1)[1].split('P_COUNT',1)[0].replace('\n','').split(',') if x.strip()]
keys=['P_GHOST']+keys
base_trace={0:'target[LENGTH] -> controls.ms -> region',1:'target[GATE] -> controls.gate -> engine_tick.want',4:'punch_command -> ghost_c11_punch -> punch_left -> controls.gate',9:'target[BREAK] -> controls.fracture -> micro-slices',10:'DO_CAPTURE -> engine_capture -> banks/cap_count',11:'target[FREEZE] -> controls.freeze -> engine_tick',14:'target[REVERSE] -> controls.reverse -> signed playback speed -> region reverse boundary',36:'DO_STORE -> scene_store -> scene data',47:'DO_APPLY -> scene values -> target -> engine_control'}
for row in rows:
 p=row['parameter']
 if p<49:row['source_trace']=base_trace.get(p,'base target['+params[p]['key']+'] -> private base-render.inc controls/render/dispatch')
 elif p<124:row['source_trace']='vst.c set/receive or base_id -> params.c c1_set('+keys[p-49]+') -> core.c effective state / scheduler / Motion -> ghost_c11_config/mix -> engine_control/tick'
 else:row['source_trace']='vst.c receive clock-aware alias -> c1_set(P_RATE or P_DISTANCE) -> shared clock'
 if p==14:row['result_test']='test_reverse_ramp_is_mathematically_reversed_with_freeze'
 elif p==4:row['result_test']='test_punch_rearms_after_clean_and_clean_same_block_still_wins'
 elif p in (71,72):row['result_test']='test_motion_bounds_link_safely_and_persist'
 elif p in (76,77,55,70,9,15,16,17,12,13,53):row['result_test']='test_controls_change_audio_under_known_conditions_and_fixed_seed'
 elif p in (36,47):row['result_test']='test_scene_store_apply_is_a_real_restoration'
 else:row['result_test']='test_each_noncommand_gui_binding_accepts_a_real_state_change + C1 core suites; command/conditional semantics in matrix'
(out/'functional-controls.json').write_text(json.dumps(report,indent=2)+'\n')
program_details=[{'qlink':key,'parameter':p,'label':by[p]['name'],'dependency':by[p]['condition'],'visible_controls':[{'view':w['view'],'bounds':w['bounds'],'acceptsHWFocus':w['focus']} for w in widgets if w['parameter']==p and w['type'] in defs],'highlight':'No universal rectangle: parameter may be off-page. Host Program Mode focus PENDING.'} for key,p in q['Program Mode Q-Links'].items()]
(out/'functional-qlinks.json').write_text(json.dumps({'screen':qrows,'program':q['Program Mode Q-Links'],'program_details':program_details,'physical_validation':'PENDING'},indent=2)+'\n')
(out/'functional-dependencies.json').write_text(json.dumps(matrix,indent=2)+'\n')
with (out/'functional-controls.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['id','view','parameter','parameter_name','bounds','hitbox','touch_event','gesture','callback','state','dependency','visual','persistence','source_trace','result_test','validation'],extrasaction='ignore');writer.writeheader();writer.writerows(rows)
canvas=Image.new('RGB',(1920,1200),'#090e11')
for i,p in enumerate(sorted((out/'previews').glob('[0-9][0-9]-*.png'))):canvas.paste(Image.open(p).resize((640,400)),((i%3)*640,(i//3)*400))
canvas.save(out/'previews/contact-sheet.png')
(out/'functional-provenance.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [ROOT/'experiments/ghost-c1'/n for n in ['vst.c','core.c','params.c','engine.c','base.c','prepare.py']]+[ROOT/'experiments/ghost-product/build.py',ROOT/'experiments/ghost-product/audit_functional.py',ROOT/'tools/ghost_functional_trial.py',ROOT/'tools/ghost-product-transaction.sh',ROOT/'tests/test_ghost_functional_audit.py',ROOT/'tests/ghost_functional_core.c',ROOT/'tests/test_ghost_functional_transaction.py',ROOT/'experiments/ghost-product/run_sanitizers.py',ROOT/'experiments/ghost-product/run_rt_guard.py',ROOT/'experiments/ghost-product/inspect_gui.py',ROOT/'experiments/ghost-product/render_functional.py',ROOT/'experiments/ghost-c12-2/build_independent_ghost.py',ROOT/'src/engine.c',ROOT/'src/plugin.c',ROOT/'tools/ghost_product.py']},indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('rows','indicators_and_navigation')},indent=2))
if errors:raise SystemExit(1)
