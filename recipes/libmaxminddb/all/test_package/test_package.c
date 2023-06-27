#include <maxminddb.h>
#include <stdio.h>

int main() {
    printf("version: %s\n", MMDB_lib_version());
    return 0;
}
