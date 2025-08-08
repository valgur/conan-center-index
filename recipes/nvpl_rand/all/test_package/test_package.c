#include <nvpl_rand.h>
#include <stdio.h>

int main() {
    int version;
    nvplRandStatus_t status = nvplRandGetVersion(&version);
    if (status != NVPL_RAND_STATUS_SUCCESS) {
        fprintf(stderr, "Failed to get nvpl_rand version: %d\n", status);
        return 1;
    }
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
    printf("nvpl_rand version: %d.%d.%d\n", major, minor, patch);
}
