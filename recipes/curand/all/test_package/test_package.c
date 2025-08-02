#include <curand.h>
#include <stdio.h>

int main() {
    int version;
    curandStatus_t status = curandGetVersion(&version);
    if (status != CURAND_STATUS_SUCCESS) {
        printf("cuRAND API error: %d\n", status);
        return 1;
    }
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
    printf("cuRAND version: %d.%d.%d\n", major, minor, patch);
}
