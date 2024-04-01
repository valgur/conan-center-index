#include <SuiteSparse_config.h>

#include <stdio.h>
#include <string.h>

int main (void)
{
    int version[3];
    SuiteSparse_version(version);
    printf("SuiteSparse version: %d.%d.%d (%s)\n", version[0], version[1], version[2], SUITESPARSE_DATE) ;
}
