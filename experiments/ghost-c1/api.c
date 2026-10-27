/* SPDX-License-Identifier: GPL-3.0-only. Allocation occurs only at instance lifecycle. */
#include "c1.h"
#include <stdlib.h>
void *ghost_c1_create(double rate){C1 *c=calloc(1,sizeof(C1Audio));if(c&&!c1_init(c,rate)){free(c);return NULL;}if(c)c1_bind(c,&((C1Audio*)c)->engine,1);return c;}
void ghost_c1_destroy(void *c){free(c);}
int ghost_c1_set(void *c,unsigned p,float v){return c&&c1_set(c,p,v);}
float ghost_c1_get(const void *c,unsigned p){return c?c1_get(c,p):0;}
unsigned ghost_c1_process(void *c,const float *l,const float *r,float *ol,float *or,unsigned n,C1Trace *t,unsigned cap){return c?c1_process(c,l,r,ol,or,n,t,cap):0;}
size_t ghost_c1_save(const void *c,unsigned char *b,size_t n){return c?c1_save(c,b,n):0;}
int ghost_c1_load(void *c,const unsigned char *b,size_t n){return c&&c1_load(c,b,n);}
