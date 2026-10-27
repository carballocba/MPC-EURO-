/* SPDX-License-Identifier: GPL-3.0-only. Explicit little-endian TLV, no struct dumps. */
#include "c1.h"
#include "../../build/params.h"
#include <string.h>
#include <math.h>
static void u32(unsigned char *b,uint32_t x){for(unsigned i=0;i<4;++i)b[i]=(unsigned char)(x>>(i*8));}
static uint32_t r32(const unsigned char *b){return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
static uint32_t checksum(const unsigned char *b,size_t n){uint32_t x=2166136261u;for(size_t i=0;i<n;++i)x=(x^b[i])*16777619u;return x;}
/* Canonical scalar walk; booleans/enums decoded only if exactly integral. */
static unsigned flatten(C1State *s,float *v,int read){unsigned n=0;
#define F(x) do{if(read){x=v[n];}else v[n]=(float)(x);++n;}while(0)
#define U(x) do{if(read){if(!isfinite(v[n])||v[n]<0||v[n]>65535||v[n]!=floorf(v[n]))return 0;x=(unsigned)v[n];}else v[n]=(float)(x);++n;}while(0)
 U(s->event.enabled);U(s->event.beat_sync);U(s->event.density);U(s->event.rotation);U(s->event.seed);F(s->event.distance);F(s->event.probability);F(s->event.duration_ms);F(s->event.rest_ms);F(s->event.jitter);F(s->event.capture_cooldown_ms);
 for(unsigned d=0;d<C1_DESTS;++d){GDestination *r=&s->random[d];U(r->enabled);U(r->interval);F(r->probability);F(r->minimum);F(r->maximum);F(r->depth);F(r->smooth_ms);U(s->locked[d]);F(s->manual[d]);MRoute *m=&s->route[d];U(m->enabled);U(m->source);F(m->depth);F(m->minimum);F(m->maximum);F(m->probability);F(m->smooth_ms);}
 for(unsigned i=0;i<8;++i){MConfig *m=&s->source[i];U(m->type);U(m->sync);U(m->hold);U(m->seed);F(m->rate);F(m->depth);F(m->minimum);F(m->maximum);F(m->probability);}
 U(s->motion);U(s->buffer);U(s->chaos_on);U(s->listen);U(s->listen_capture);U(s->listen_repeat);U(s->quantized);F(s->chaos);F(s->sensitivity);F(s->spacing);F(s->listen_probability);U(s->destination);U(s->motion_destination);U(s->source_selected);
#undef F
#undef U
 return n;}
size_t c1_save(const C1 *c,unsigned char *out,size_t capacity){float values[320];C1State state=c->state;state.manual[C1_CAPTURE]=state.manual[C1_FREEZE]=state.manual[C1_GATE]=0;unsigned n=flatten(&state,values,0);size_t size=44+4*n+(state.legacy_size?8+state.legacy_size:0);if(!out||capacity<size)return size;
 memcpy(out,"GHC1",4);u32(out+4,1);u32(out+8,(uint32_t)size);u32(out+12,1);u32(out+16,4*n);for(unsigned i=0;i<n;++i){uint32_t bits;memcpy(&bits,&values[i],4);u32(out+20+4*i,bits);}size_t pos=20+4*n;u32(out+pos,2);u32(out+pos+4,8);uint64_t distance;memcpy(&distance,&state.event.distance,8);u32(out+pos+8,(uint32_t)distance);u32(out+pos+12,(uint32_t)(distance>>32));pos+=16;
 if(state.legacy_size){u32(out+pos,3);u32(out+pos+4,state.legacy_size);memcpy(out+pos+8,state.legacy_blob,state.legacy_size);pos+=8+state.legacy_size;}
 u32(out+pos,0);u32(out+size-4,checksum(out,size-4));return size;}
static int valid_br(const unsigned char *in,size_t size){
 unsigned count=size==48?8:49;
 if((size!=48&&size!=532)||memcmp(in,size==48?"EBR1":"EBR2",4)||r32(in+4)!=(size==48?1u:2u)||r32(in+8)!=0x45754272u||r32(in+size-4)!=checksum(in,size-4))return 0;
 for(unsigned i=0;i<count;++i){uint32_t bits=r32(in+12+4*i);float x;memcpy(&x,&bits,4);if(!isfinite(x)||x<0||x>1||(!PARAMS[i].saved&&x!=0))return 0;
  if(PARAMS[i].saved&&PARAMS[i].nopts&&fabsf(x*(PARAMS[i].nopts-1)-roundf(x*(PARAMS[i].nopts-1)))>.00001f)return 0;}
 if(size==532)for(unsigned i=12+49*4;i<size-4;i+=4){uint32_t bits=r32(in+i);float x;memcpy(&x,&bits,4);unsigned field=((i-12-49*4)/4)%E_FIELDS;if(!isfinite(x)||x<0||x>1||((field==5||field==8)&&x!=0&&x!=1)||(field==7&&fabsf(x*10-roundf(x*10))>.00001f))return 0;}
 return 1;
}
static int import_br(C1 *c,const unsigned char *in,size_t size){
 if(!valid_br(in,size))return 0;unsigned count=size==48?8:49;float values[49]={0};for(unsigned i=0;i<count;++i){uint32_t bits=r32(in+12+4*i);memcpy(&values[i],&bits,4);}
 C1State s=c1_defaults();s.manual[0]=5+445*values[0];s.manual[10]=values[2];if(count>8){s.manual[1]=values[9];s.manual[4]=values[12];s.manual[5]=50+1950*values[13];s.manual[6]=values[14];s.manual[7]=-24+48*values[15];s.manual[8]=-12+24*values[16];s.manual[9]=values[17];}
 memcpy(s.legacy_blob,in,size);s.legacy_size=(unsigned)size;return c1_apply(c,&s);
}
int c1_load(C1 *c,const unsigned char *in,size_t size){if(!in)return 0;if(size>=4&&(!memcmp(in,"EBR1",4)||!memcmp(in,"EBR2",4)))return import_br(c,in,size);
 if(size<28||size>65536||memcmp(in,"GHC1",4)||r32(in+4)!=1||r32(in+8)!=size||r32(in+size-4)!=checksum(in,size-4))return 0;
 C1State state=c1_defaults();float v[320],dummy[320];unsigned expected=flatten(&state,dummy,0),seen=0,seen_distance=0,seen_legacy=0;double distance=0;size_t pos=12;
 while(pos+8<=size-4){unsigned id=r32(in+pos),len=r32(in+pos+4);pos+=8;if(len>size-4-pos)return 0;
  if(id==1){if(seen||len!=expected*4)return 0;for(unsigned i=0;i<expected;++i){uint32_t bits=r32(in+pos+i*4);memcpy(&v[i],&bits,4);}if(flatten(&state,v,1)!=expected)return 0;seen=1;}
  else if(id==2){if(seen_distance||len!=8)return 0;uint64_t bits=(uint64_t)r32(in+pos)|(uint64_t)r32(in+pos+4)<<32;memcpy(&distance,&bits,8);seen_distance=1;}
  else if(id==3){if(seen_legacy||(len!=48&&len!=532))return 0;memcpy(state.legacy_blob,in+pos,len);state.legacy_size=len;seen_legacy=1;}
  pos+=len;
 }
 if(seen_distance)state.event.distance=distance;
 if(pos+4!=size-4||r32(in+pos)!=0||!seen||!c1_valid(&state))return 0;
 if(state.legacy_size){if(!valid_br(state.legacy_blob,state.legacy_size))return 0;}
 if(!c1_apply(c,&state))return 0;ghost_reset(&c->clock);memset(c->source,0,sizeof c->source);c->origin_sample=c->clock.sample;c->origin_beat=c->clock.beat;c->dice_index=0;c->dice_mask=c->manual_mask=c->pending_capture=0;c->automation_mask=0;memset(c->manual_until,0,sizeof c->manual_until);return 1;}
int c1_import_c0(C1 *c,const GAudio *a){if(!c||!a)return 0;C1State s=c1_defaults();s.event=a->ghost.config;for(unsigned d=0;d<4;++d)s.random[d]=s.event.destination[d];const EConfig *m=&a->ghost.manual;s.manual[0]=m->ms;s.manual[1]=m->fracture;s.manual[4]=m->position;s.manual[5]=m->buffer_ms;s.manual[6]=m->reverse;s.manual[7]=m->bend;s.manual[8]=m->pitch;s.manual[9]=m->corrupt;s.manual[10]=a->target_mix;s.quantized=m->quantized;return c1_apply(c,&s);}
