#include <nccl.h>
#include <stdio.h>

int main() {
    int version;
    ncclResult_t status = ncclGetVersion(&version);
    if (status != ncclSuccess) {
        printf("NCCL error: %s\n", cudaGetErrorString(status));
        return 1;
    }
    int major = version / 10000;
    int minor = version % 10000 / 100;
    int patch = version % 100;
    printf("NCCL version: %d.%d.%d\n", major, minor, patch);
}
