/* GPL-3.0-only. Additional programs; original indices 0..7 remain unchanged.
 * Called on a temporary preset state, never mutates the running audio owner. */
static const char *product_names[]={"Ghost Scatter","Dust and Gaps","Breathing Tape","Buffer Drift","Percussive Listen","Chaos Cuts","Pitch Mutations","Live Canvas"};
static void product_preset(C1 *c,unsigned id){
 C1State s=c1_defaults();s.event.seed=23+id*17;s.manual[C1_MIX]=.75f;
 s.destination=s.motion_destination=s.source_selected=0;
 s.route[0].enabled=1;s.route[0].minimum=40;s.route[0].maximum=180;
 if(id!=4&&id!=7){s.event.enabled=1;s.event.density=8;s.event.probability=.8f;s.event.duration_ms=90;
  s.random[0].enabled=1;s.random[0].minimum=15;s.random[0].maximum=110;
 }
 switch(id){
 case 0:s.random[1].enabled=1;s.random[1].minimum=.1f;s.random[1].maximum=.6f;break;
 case 1:s.event.density=3;s.event.duration_ms=30;s.event.rest_ms=80;s.manual[C1_BREAK]=.65f;s.random[0].minimum=8;s.random[0].maximum=40;break;
 case 2:s.motion=1;s.event.density=16;s.event.duration_ms=400;s.random[0].enabled=0;s.source[0].type=M_SINE;s.source[0].rate=1500;s.source[0].depth=.7f;
  s.route[C1_BEND].enabled=1;s.route[C1_BEND].source=0;s.route[C1_BEND].minimum=-4;s.route[C1_BEND].maximum=4;break;
 case 3:s.motion=1;s.event.duration_ms=240;s.random[C1_POSITION].enabled=1;s.random[C1_FREEZE].enabled=1;s.random[C1_FREEZE].probability=.4f;
  s.route[C1_POSITION].enabled=1;s.route[C1_POSITION].source=1;s.source[1].type=M_SMOOTH;s.source[1].rate=800;break;
 case 4:s.listen=1;s.sensitivity=2;s.spacing=120;s.event.duration_ms=100;break;
 case 5:s.chaos_on=1;s.chaos=.75f;s.event.density=12;s.random[1].enabled=1;s.random[C1_CORRUPT].enabled=1;s.random[C1_CORRUPT].minimum=.1f;s.random[C1_CORRUPT].maximum=.4f;break;
 case 6:s.event.density=6;s.random[C1_PITCH].enabled=1;s.random[C1_PITCH].minimum=-7;s.random[C1_PITCH].maximum=7;s.locked[C1_MIX]=1;break;
 default:s.manual[C1_MIX]=1;break;
 }
 /* Continuous ranges are shared by the random and Motion editors. */
 for(unsigned d=0;d<C1_DESTS;++d)if(s.random[d].enabled){s.route[d].minimum=s.random[d].minimum;s.route[d].maximum=s.random[d].maximum;}
 c1_apply(c,&s);
}
