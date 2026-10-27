/* Darwin-only test adapter for GNU ld --wrap's __real_* side. */
#include <stdlib.h>
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdarg.h>
void *__real_malloc(size_t n) { return malloc(n); }
void *__real_calloc(size_t n,size_t s) { return calloc(n,s); }
void *__real_realloc(void *p,size_t n) { return realloc(p,n); }
void __real_free(void *p) { free(p); }
int __real_pthread_mutex_lock(pthread_mutex_t *p) { return pthread_mutex_lock(p); }
int __real_pthread_mutex_trylock(pthread_mutex_t *p) { return pthread_mutex_trylock(p); }
int __real_pthread_mutex_unlock(pthread_mutex_t *p) { return pthread_mutex_unlock(p); }
int __real_pthread_join(pthread_t p,void **r) { return pthread_join(p,r); }
int __real_open(const char *s,int f,...) {
    if(f&O_CREAT) { va_list a;va_start(a,f);int m=va_arg(a,int);va_end(a);return open(s,f,m); }
    return open(s,f);
}
FILE *__real_fopen(const char *s,const char *m) { return fopen(s,m); }
ssize_t __real_read(int f,void *b,size_t n) { return read(f,b,n); }
ssize_t __real_write(int f,const void *b,size_t n) { return write(f,b,n); }
