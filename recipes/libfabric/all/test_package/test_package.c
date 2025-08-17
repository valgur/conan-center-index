#include <rdma/fabric.h>
#include <stdio.h>

int main () {
    uint32_t version = fi_version();
    printf("libfabric version: %d.%d\n", FI_MAJOR(version), FI_MINOR(version));
}
