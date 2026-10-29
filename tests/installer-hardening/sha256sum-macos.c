#include <CommonCrypto/CommonDigest.h>
#include <stdio.h>
#include <string.h>
int sum(const char *p,char *out){FILE*f=!strcmp(p,"-")?stdin:fopen(p,"rb");if(!f)return 1;CC_SHA256_CTX c;CC_SHA256_Init(&c);unsigned char b[16384],d[32];size_t n;while((n=fread(b,1,sizeof b,f)))CC_SHA256_Update(&c,b,(CC_LONG)n);if(f!=stdin)fclose(f);CC_SHA256_Final(d,&c);for(int i=0;i<32;i++)sprintf(out+2*i,"%02x",d[i]);return 0;}
int main(int n,char**v){char h[65];int ret=0;if(n==3&&!strcmp(v[1],"-c")){FILE*f=!strcmp(v[2],"-")?stdin:fopen(v[2],"r");if(!f)return 1;char line[8192];while(fgets(line,sizeof line,f)){line[strcspn(line,"\r\n")]=0;if(strlen(line)<67)return 1;if(sum(line+66,h)||strncmp(line,h,64))ret=1;}if(f!=stdin)fclose(f);return ret;}if(n!=2||sum(v[1],h))return 1;printf("%s  %s\n",h,v[1]);return 0;}
