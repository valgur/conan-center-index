#include <ucc/api/ucc.h>
#include <stdio.h>

int main() {
    unsigned major, minor, release;
    ucc_get_version(&major, &minor, &release);
    printf("UCC version: %u.%u.%u\n", major, minor, release);
}
