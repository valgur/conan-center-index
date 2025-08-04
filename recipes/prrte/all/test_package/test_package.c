#include <pmix.h>
#include <prte.h>
#include <stdio.h>

int main(int argc, char **argv) {
    PMIx_Init(NULL, NULL, 0);
    printf("PRRTE version: %d.%d.%d\n", PRTE_VERSION_MAJOR, PRTE_VERSION_MINOR, PRTE_VERSION_RELEASE);
}
