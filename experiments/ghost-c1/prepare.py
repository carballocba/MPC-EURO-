"""Audited private integration copy. Protected production source is never edited."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-c11-demo';OUT.mkdir(exist_ok=True)
s=(ROOT/'src/plugin.c').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,('upstream integration anchor changed',a[:70]);s=s.replace(a,b)
s=s.replace('Midi midi[64]','Midi midi[1024]').replace('Midi events[64]','Midi events[1024]').replace('ne<64','ne<1024').replace('&63','&1023').replace('numEvents>63','numEvents>1023')
replace('    /* Host event lists need not be sorted; fixed 63-event insertion sort. */\n    for(unsigned i=1;i<ne;++i) {Midi m=events[i];unsigned j=i;while(j && events[j-1].delta>m.delta){events[j]=events[j-1];--j;}events[j]=m;}','    ghost_c11_sort(events,ne);')
replace('typedef struct { int delta; unsigned char status,note,velocity; } Midi;', '''typedef struct { int delta; unsigned char status,note,velocity; } Midi;
/* Stable fixed-storage radix sort, bounded O(4*(N+256)); no qsort/heap. */
static void ghost_c11_sort(Midi *events,unsigned n){
    if(n<2)return;Midi temporary[1024];
    for(unsigned shift=0;shift<32;shift+=8){unsigned count[256]={0},offset[256];
        for(unsigned i=0;i<n;++i)++count[((unsigned)events[i].delta>>shift)&255];
        unsigned sum=0;for(unsigned i=0;i<256;++i){offset[i]=sum;sum+=count[i];}
        for(unsigned i=0;i<n;++i)temporary[offset[((unsigned)events[i].delta>>shift)&255]++]=events[i];
        memcpy(events,temporary,n*sizeof(*events));
    }
}''')
replace('        while(event<ne && events[event].delta<=k) {midi_action(p,events[event++]);changed=1;}', '''        while(event<ne && events[event].delta<=k) {midi_action(p,events[event++]);changed=1;}
        changed |= ghost_c11_tick(fx,clean(in&&in[0]?in[0][k]:0),clean(in&&in[1]?in[1][k]:in&&in[0]?in[0][k]:0),(unsigned)k,changed);
        if(ghost_c11_capture_request(fx))atomic_fetch_or(&p->commands,DO_CAPTURE);''')
replace('            if(cmd&DO_CAPTURE)engine_capture(&p->engine);','            if(cmd&DO_CAPTURE)ghost_c11_capture_result(fx,engine_capture(&p->engine));')
replace('EConfig c=controls(p);if(bypass', 'EConfig c=controls(p);ghost_c11_config(fx,&c);if(bypass')
replace('            if(punch==1)p->punch_left=(unsigned)ceilf(rate*.45f);else if(punch==2)p->punch_left=0;', '''            if(punch==1){
                ghost_c11_punch(fx);
                p->punch_left=(unsigned)ceilf(rate*.45f);
                /* A new punch takes current live audio, not an old snapshot.
                 * Freeze intentionally keeps the held capture. O(1), no copies. */
#ifndef GHOST_BUFFER_ENGINE
                if(!option(p,FREEZE) && !p->engine.r.base.freeze && !(p->engine.r.playing && p->engine.r.voice.bank==(int)p->engine.r.live))
                    ghost_c11_capture_result(fx,engine_capture(&p->engine));
#endif
            }else if(punch==2)p->punch_left=0;''')
replace('mix_target=load(p,MIX);mix_step=', 'mix_target=ghost_c11_mix(fx,load(p,MIX));mix_step=')
# Overflow is all-or-nothing; count valid events before publishing any.
replace('        unsigned head=atomic_load(&p->midi_head);', '''        unsigned head=atomic_load(&p->midi_head),tail=atomic_load_explicit(&p->midi_tail,memory_order_acquire),valid=0;
        for(int i=0;i<list->numEvents;++i){VstMidiEvent *m=(VstMidiEvent*)events[i];if(m&&m->type==1&&m->byteSize>=(int)sizeof(*m))++valid;}
        if(valid>1023-((head-tail)&1023))return 0;''')
replace('            head=next;atomic_store_explicit(&p->midi_head,head,memory_order_release);','            head=next;')
replace('        }return 1;\n    }\n    case effGetChunk:', '        }atomic_store_explicit(&p->midi_head,head,memory_order_release);return 1;\n    }\n    case effGetChunk:')
(OUT/'base-render.inc').write_text(s)

# Private GHOST reverse boundary correction. Preserve src/engine.c and BeatRepeat.
e=(ROOT/'src/engine.c').read_text()
a='EVoice v={(int)r->captured,(r->cap_start+skip)%r->capacity,length,0};'
b='EVoice v={(int)r->captured,(r->cap_start+skip)%r->capacity,length,(r->effective.reverse!=r->cycle_reverse)?(double)(length-1):0};'
assert e.count(a)==1,'engine reverse-region integration anchor changed'
(OUT/'engine-render.inc').write_text(e.replace(a,b))
