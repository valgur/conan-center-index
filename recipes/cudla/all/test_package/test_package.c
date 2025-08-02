#include <cudla.h>
#include <stdio.h>

int main() {
    uint64_t version;
    cudlaStatus status = cudlaGetVersion(&version);
    if (status != cudlaSuccess) {
        printf("cudla API error: %d\n", status);
        return 1;
    }
    int major = version / 1000000;
    int minor = (version % 1000000) / 1000;
    int patch = version % 1000;
    printf("cuDLA version: %d.%d.%d\n", major, minor, patch);
}
