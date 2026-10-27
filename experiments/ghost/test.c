/* SPDX-License-Identifier: GPL-3.0-only. Native offline acceptance tests. */
#include "audio.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned tests;
#define TEST(f) do {f();++tests;printf("PASS %s\n",#f);} while(0)
static GConfig enabled(void) {GConfig c=ghost_defaults();c.enabled=1;c.beat_sync=0;c.distance=20;c.density=16;c.probability=1;c.duration_ms=5;c.rest_ms=0;return c;}
static GDestination dest(float lo,float hi) {return (GDestination){1,1,1,lo,hi,1,0};}
static GFrame tick(Ghost *g) {GFrame f;ghost_tick(g,&f);return f;}
static void test_validation_atomic(void) {
 Ghost g;assert(!ghost_init(&g,NAN));assert(!ghost_init(&g,15999));assert(ghost_init(&g,44100));
 GConfig c=enabled();assert(ghost_configure(&g,&c));Ghost before=g;
 c.destination[0]=dest(400,5);assert(!ghost_configure(&g,&c));assert(!memcmp(&g,&before,sizeof g));
 c=enabled();c.duration_ms=NAN;assert(!ghost_configure(&g,&c));
 c=enabled();c.destination[2].smooth_ms=1;assert(!ghost_configure(&g,&c));
 EConfig m=g.manual;m.buffer_ms=INFINITY;assert(!ghost_manual(&g,&m,0));assert(!memcmp(&g,&before,sizeof g));
 assert(!ghost_clock(&g,120,1,1,NAN));assert(!memcmp(&g,&before,sizeof g));
}
static void test_density_probability_distinct(void) {
 for(unsigned d=0;d<=16;++d) {
  Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.distance=5;c.density=d;c.duration_ms=.1f;assert(ghost_configure(&g,&c));
  unsigned opportunities=0,eligible=0,accepted=0;
  for(unsigned k=0;k<1280;++k) {GFrame f=tick(&g);opportunities+=(f.flags&G_OPPORTUNITY)!=0;eligible+=f.eligible;accepted+=f.accepted;}
  assert(opportunities==16&&eligible==d&&accepted==d);
 }
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.probability=0;assert(ghost_configure(&g,&c));
 for(unsigned k=0;k<16000;++k)assert(!tick(&g).active);
}
static void test_probability_statistics(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.distance=5;c.duration_ms=.1f;c.probability=.5f;assert(ghost_configure(&g,&c));
 unsigned accepted=0;for(unsigned k=0;k<8000000;++k)accepted+=tick(&g).accepted;
 assert(accepted>49000&&accepted<51000);
}
static void test_rng_domains_and_ranges(void) {
 Ghost a,b;ghost_init(&a,16000);ghost_init(&b,16000);GConfig ca=enabled(),cb=ca;
 ca.destination[G_LENGTH]=dest(125,200);ca.destination[G_BREAK]=dest(.2f,.4f);ca.destination[G_LENGTH].smooth_ms=3;
 cb=ca;cb.destination[G_LENGTH].enabled=0;assert(ghost_configure(&a,&ca));assert(ghost_configure(&b,&cb));
 for(unsigned k=0;k<32000;++k) {
  GFrame fa=tick(&a),fb=tick(&b);assert(fa.accepted==fb.accepted);
  assert(fa.effective.fracture==fb.effective.fracture);
  if(fa.active){assert(fa.effective.ms>=125&&fa.effective.ms<=200);assert(fa.effective.fracture>=.2f&&fa.effective.fracture<=.4f);}
 }
 assert(ghost_random(1,0,4)!=ghost_random(1,0,5));assert(ghost_random(1,0,4)!=ghost_random(2,0,4));
}
static void test_destination_divider_and_zero_depth(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.destination[0]=dest(200,300);c.destination[0].depth=0;
 c.destination[1]=dest(1,1);c.destination[1].interval=3;assert(ghost_configure(&g,&c));
 for(unsigned k=0;k<16000;++k){GFrame f=tick(&g);assert(f.effective.ms==100);if(f.flags&G_START)assert(f.effective.fracture==(f.opportunity%3?0:1));}
}
static void test_duration_rest_and_capture_cooldown(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.distance=10;c.duration_ms=100;c.rest_ms=12;c.destination[2]=dest(0,1);c.capture_cooldown_ms=100;
 assert(ghost_configure(&g,&c));unsigned active=0,captures=0,starts=0;
 for(unsigned k=0;k<16000;++k){GFrame f=tick(&g);active+=f.active;captures+=(f.flags&G_CAPTURE_PULSE)!=0;starts+=f.accepted;}
 assert(active<16000*.4&&starts>30&&starts<40&&captures<=10);
}
static void test_manual_ownership_and_off(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.destination[3]=dest(0,1);c.destination[0]=dest(200,200);assert(ghost_configure(&g,&c));
 assert(tick(&g).automatic_freeze);EConfig m=g.manual;m.freeze=1;m.ms=75;
 assert(ghost_manual(&g,&m,(1u<<G_FREEZE)|(1u<<G_LENGTH)));
 GFrame f=tick(&g);assert(f.effective.freeze&&f.effective.ms==75);
 while(g.sample<100)f=tick(&g);assert(!f.active&&f.effective.freeze&&g.manual.freeze);
 c.enabled=0;assert(ghost_configure(&g,&c));f=tick(&g);assert(!f.active&&f.effective.freeze&&f.effective.ms==75);
}
static void test_override_expires_next_event(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.destination[0]=dest(200,200);assert(ghost_configure(&g,&c));tick(&g);
 EConfig m=g.manual;m.ms=75;ghost_manual(&g,&m,1u<<G_LENGTH);assert(tick(&g).effective.ms==75);
 GFrame f;do{f=tick(&g);}while(!(f.flags&G_START));assert(f.effective.ms==200&&g.manual.ms==75);
}
static void test_clean_wins_same_boundary(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.destination[3]=dest(0,1);assert(ghost_configure(&g,&c));tick(&g);
 ghost_clean(&g);ghost_capture(&g);assert(ghost_configure(&g,&c));
 EConfig m=g.manual;m.freeze=m.gate=m.run=1;ghost_manual(&g,&m,31);
 GFrame f=tick(&g);assert(f.flags&G_CLEAN);assert(!(f.flags&G_CAPTURE_PULSE));assert(!f.active&&!f.effective.gate&&!f.effective.freeze&&!f.effective.run&&!g.config.enabled);
}
static void test_clock_seek_stop_fallback(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.beat_sync=1;c.distance=.25;assert(ghost_configure(&g,&c));assert(tick(&g).active);
 EConfig m=g.manual;m.gate=1;ghost_manual(&g,&m,0);ghost_clock(&g,120,0,0,0);
 double beat=g.beat;for(unsigned k=0;k<1000;++k){GFrame f=tick(&g);assert(!f.active&&f.effective.gate);}assert(g.beat==beat);
 ghost_clock(&g,150,1,1,1000);GFrame f=tick(&g);assert(f.flags&G_START);assert(g.opportunity==2);assert(g.beat>1000);
 ghost_clock(&g,NAN,1,0,0);assert(g.fallback&&g.tempo==120);
}
static void test_duration_ms_survives_tempo_change(void) {
 Ghost g;ghost_init(&g,16000);GConfig c=enabled();c.beat_sync=1;c.distance=1;c.duration_ms=100;assert(ghost_configure(&g,&c));tick(&g);
 ghost_clock(&g,240,1,0,0);GFrame f;do{f=tick(&g);}while(f.active);assert(f.sample==1600);
}
static void test_reset_and_jitter(void) {
 Ghost a,b;ghost_init(&a,16000);ghost_init(&b,16000);GConfig c=enabled();c.jitter=.4;c.destination[0]=dest(10,120);
 assert(ghost_configure(&a,&c));assert(ghost_configure(&b,&c));for(unsigned i=0;i<1000;++i)tick(&a);ghost_reset(&a);
 for(unsigned k=0;k<16000;++k){GFrame x=tick(&a),y=tick(&b);assert((x.flags&~(k?0u:G_END))==y.flags);assert(x.accepted==y.accepted);assert(x.effective.ms==y.effective.ms);}
}
static void test_grid_manual_preserved(void) {
 Ghost g;ghost_init(&g,16000);EConfig m=g.manual;m.time_grid=1;m.grid=8;ghost_manual(&g,&m,0);
 GConfig c=enabled();c.destination[0]=dest(5,15);assert(ghost_configure(&g,&c));GFrame f=tick(&g);assert(f.effective.grid==8&&f.effective.ms==100);
}
static void test_clock_thirty_minute_drift(void) {
 Ghost g;ghost_init(&g,44100);GConfig c=enabled();c.beat_sync=1;c.distance=.25;c.duration_ms=1;c.probability=0;
 assert(ghost_configure(&g,&c));ghost_clock(&g,123,1,0,0);unsigned seen=0;
 for(uint64_t k=0;k<UINT64_C(44100)*1800;++k) {
  GFrame f=tick(&g);if(f.flags&G_OPPORTUNITY){double ideal=ceil((double)f.opportunity*.25*60*44100/123);assert(fabs((double)f.sample-ideal)<=1);++seen;}
 }
 assert(seen==14760);
}
static void test_audio_block_invariance(void) {
 const unsigned n=32000;GAudio *a=calloc(1,sizeof(*a)),*b=calloc(1,sizeof(*b));float *in=malloc(n*4),*al=malloc(n*4),*ar=malloc(n*4),*bl=malloc(n*4),*br=malloc(n*4);
 assert(a&&b&&in&&al&&ar&&bl&&br);ghost_audio_init(a,16000);ghost_audio_init(b,16000);
 GConfig c=enabled();c.destination[0]=dest(10,90);c.destination[1]=dest(0,.5f);c.destination[2]=dest(0,1);c.destination[3]=dest(0,1);c.jitter=.3;assert(ghost_configure(&a->ghost,&c));assert(ghost_configure(&b->ghost,&c));
 for(unsigned k=0;k<n;++k)in[k]=.2f*sinf(k*.1f);
 GTrace ta[1000],tb[1000];unsigned na=ghost_audio_process(a,in,NULL,al,ar,n,ta,1000),nb=0;
 const unsigned blocks[]={1,17,32,127,512,511,1000};unsigned offset=0,i=0;
 while(offset<n){unsigned size=blocks[i++%7];if(size>n-offset)size=n-offset;nb+=ghost_audio_process(b,in+offset,NULL,bl+offset,br+offset,size,tb+nb,1000-nb);offset+=size;}
 assert(!memcmp(al,bl,n*4)&&!memcmp(ar,br,n*4)&&na==nb);
 for(unsigned k=0;k<na;++k){assert(ta[k].sample==tb[k].sample&&ta[k].flags==tb[k].flags&&ta[k].length_ms==tb[k].length_ms&&ta[k].fracture==tb[k].fracture&&ta[k].capture_result==tb[k].capture_result);}
 assert(!a->trace_dropped&&!b->trace_dropped);free(a);free(b);free(in);free(al);free(ar);free(bl);free(br);
}
static float slew(float x,float y,float step){return x<y?fminf(x+step,y):fmaxf(x-step,y);}
static void test_off_matches_unmodified_engine_reference(void) {
 GAudio *a=calloc(1,sizeof(*a));Engine *e=calloc(1,sizeof(*e));assert(a&&e);ghost_audio_init(a,44100);engine_reset(e,44100,1);
 EConfig m=ghost_manual_defaults();m.gate=1;m.fracture=.3f;m.corrupt=.2f;m.pitch=-3;
 ghost_manual(&a->ghost,&m,0);float depth=0,release[2]={0};
 for(unsigned k=0;k<24000;++k) {
  int change=k==0||k==10000||k==12000;
  if(k==10000)m.gate=0;if(k==12000){m.gate=1;m.ms=33;}
  if(change)ghost_manual(&a->ghost,&m,0);
  if(!(k&31)||change)engine_control(e,&m);
  float l=.2f*sinf(k*.05f),r=.3f*cosf(k*.07f),wl,wr,ol,or;
  engine_tick(e,l,r,120,&wl,&wr);
  if(e->r.playing){release[0]=wl;release[1]=wr;}else if(depth>0){wl=release[0];wr=release[1];}
  depth=slew(depth,e->r.playing?1:0,1.f/(44100*.005f));
  ghost_audio_process(a,&l,&r,&ol,&or,1,NULL,0);
  assert(ol==l*(1-depth)+wl*depth&&or==r*(1-depth)+wr*depth);
 }
 free(a);free(e);
}
static void test_capture_clean_and_finiteness(void) {
 const double rates[]={16000,44100,48000,96000};
 for(unsigned j=0;j<4;++j){GAudio *a=calloc(1,sizeof(*a));assert(a);ghost_audio_init(a,rates[j]);float in[512],out[512];for(unsigned i=0;i<512;++i)in[i]=.1f;
 ghost_audio_process(a,in,NULL,out,NULL,512,NULL,0);ghost_capture(&a->ghost);GTrace trace[8];ghost_audio_process(a,in,NULL,out,NULL,1,trace,8);assert(a->engine.r.cap_count==512);
 EConfig m=a->ghost.manual;m.freeze=1;ghost_manual(&a->ghost,&m,1u<<G_FREEZE);ghost_audio_process(a,in,NULL,out,NULL,512,NULL,0);
 unsigned captured=a->engine.r.cap_count;ghost_clean(&a->ghost);ghost_audio_process(a,in,NULL,out,NULL,512,NULL,0);assert(a->engine.r.cap_count==captured);assert(out[511]==in[511]);
 in[0]=NAN;in[1]=INFINITY;ghost_audio_process(a,in,NULL,out,NULL,512,NULL,0);for(unsigned i=0;i<512;++i)assert(isfinite(out[i]));free(a);}
}
static void test_bounded_trace_and_aliasing(void) {
 GAudio *a=calloc(1,sizeof(*a));assert(a);ghost_audio_init(a,16000);GConfig c=enabled();assert(ghost_configure(&a->ghost,&c));float x[1024]={0};GTrace trace[1];assert(ghost_audio_process(a,x,x,x,x,1024,trace,1)==1);assert(a->trace_dropped>0);free(a);
}
static void test_ranges_property_sweep(void) {
 for(unsigned i=0;i<200;++i){Ghost g;assert(ghost_init(&g,16000));GConfig c=enabled();c.seed=i;
  float x=(ghost_random(9,i,1)>>8)/16777216.f,y=(ghost_random(9,i,2)>>8)/16777216.f;
  float lo=fminf(x,y),hi=fmaxf(x,y);
  c.destination[0]=dest(5+445*lo,5+445*hi);c.destination[1]=dest(lo,hi);c.destination[0].smooth_ms=20;c.destination[1].smooth_ms=10;
  assert(ghost_configure(&g,&c));for(unsigned k=0;k<1000;++k){GFrame f=tick(&g);if(f.active){assert(f.effective.ms>=c.destination[0].minimum&&f.effective.ms<=c.destination[0].maximum);assert(f.effective.fracture>=lo&&f.effective.fracture<=hi);}}
 }
}
static void test_quantized_recapture_defers_safely(void) {
 GAudio *a=calloc(1,sizeof(*a));assert(a);assert(ghost_audio_init(a,16000));float in[1024],out[1024];for(unsigned i=0;i<1024;++i)in[i]=.125f;
 ghost_audio_process(a,in,NULL,out,NULL,1024,NULL,0);ghost_capture(&a->ghost);ghost_audio_process(a,in,NULL,out,NULL,1,NULL,0);
 EConfig m=a->ghost.manual;m.gate=1;m.quantized=1;assert(ghost_manual(&a->ghost,&m,0));ghost_audio_process(a,in,NULL,out,NULL,64,NULL,0);
 ghost_capture(&a->ghost);ghost_audio_process(a,in,NULL,out,NULL,1,NULL,0);assert(a->engine.r.voice.bank==(int)a->engine.r.live);
 unsigned bank=a->engine.r.live;float pinned=a->engine.ring[bank][0][0];
 ghost_capture(&a->ghost);for(unsigned i=0;i<32;++i)in[i]=.75f;
 ghost_audio_process(a,in,NULL,out,NULL,32,NULL,0);assert(a->pending_capture&&a->engine.r.count[bank]==0&&a->engine.ring[bank][0][0]==pinned);
 ghost_clean(&a->ghost);ghost_audio_process(a,in,NULL,out,NULL,1,NULL,0);assert(!a->pending_capture);free(a);
}
static void test_automatic_freeze_empty_history_primes(void) {
 GAudio *a=calloc(1,sizeof(*a));assert(a);assert(ghost_audio_init(a,16000));GConfig c=enabled();c.destination[3]=dest(0,1);assert(ghost_configure(&a->ghost,&c));
 float in[512],out[512];for(unsigned i=0;i<512;++i)in[i]=.1f;
 for(unsigned i=0;i<8;++i)ghost_audio_process(a,in,NULL,out,NULL,512,NULL,0);
 assert(a->engine.r.captured>=0&&a->engine.r.cap_count>=1600);free(a);
}
int main(void) {
 TEST(test_validation_atomic);TEST(test_density_probability_distinct);TEST(test_probability_statistics);
 TEST(test_rng_domains_and_ranges);TEST(test_destination_divider_and_zero_depth);TEST(test_duration_rest_and_capture_cooldown);
 TEST(test_manual_ownership_and_off);TEST(test_override_expires_next_event);TEST(test_clean_wins_same_boundary);
 TEST(test_clock_seek_stop_fallback);TEST(test_duration_ms_survives_tempo_change);TEST(test_reset_and_jitter);
 TEST(test_grid_manual_preserved);TEST(test_clock_thirty_minute_drift);TEST(test_audio_block_invariance);
 TEST(test_off_matches_unmodified_engine_reference);TEST(test_capture_clean_and_finiteness);TEST(test_bounded_trace_and_aliasing);
 TEST(test_ranges_property_sweep);TEST(test_quantized_recapture_defers_safely);TEST(test_automatic_freeze_empty_history_primes);
 printf("%u GHOST offline test groups passed\n",tests);return 0;
}
