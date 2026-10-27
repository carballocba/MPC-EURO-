/* GPL-3.0-only. Deterministic budget/transport checks against the real policy/clock. */
#include "performance.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
int main(void){
 for(unsigned t=0;t<4;++t)for(unsigned gi=1;gi<=4;++gi){
  unsigned long long accepted[2]={0};
  for(unsigned ch=0;ch<2;++ch){C1 *c=calloc(1,sizeof(*c));assert(c&&c1_init(c,16000));Performance p;pe_init(&p,1);pe_set(&p,PE_GLITCH,gi*.25f);pe_set(&p,PE_CHAOS,ch);c->state.event.probability=1;c->state.event.duration_ms=400;
   const double tempos[]={20,60,120,400};double tempo=tempos[t];ghost_clock(&c->clock,tempo,1,0,0);double window=60/tempo*4;unsigned samples=(unsigned)llround(window*16000),active=0;unsigned max_active=0;
   for(unsigned k=0;k<samples*12;++k){pe_tick(&p,c);active+=c->clock.active;if((k+1)%samples==0){if(active>max_active)max_active=active;assert(active<=ceil(samples*.85*gi*.25)+2);active=0;}}
   accepted[ch]=p.events;assert(isfinite(p.wet_gain)&&p.wet_gain>=0&&p.wet_gain<=1);
   ghost_clock(&c->clock,tempo,0,0,0);for(unsigned k=0;k<1000;++k)pe_tick(&p,c);assert(!c->clock.active);
   printf("tempo=%.0f glitch=%.2f chaos=%u events=%llu max_window_active=%u limit=%.1f\n",tempo,gi*.25,ch,accepted[ch],max_active,samples*.85*gi*.25);free(c);
  }assert(accepted[0]==accepted[1]);
 }
 puts("PASS 32 policy runs / per-window budgets / CHAOS-independent acceptance / host stop");return 0;
}
