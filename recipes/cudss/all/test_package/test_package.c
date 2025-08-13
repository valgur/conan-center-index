#include <cudss.h>
#include <stdio.h>

int main() {
    cudssStatus_t status = CUDSS_STATUS_SUCCESS;
    int major, minor, patch;
    status |= cudssGetProperty(MAJOR_VERSION, &major);
    status |= cudssGetProperty(MINOR_VERSION, &minor);
    status |= cudssGetProperty(PATCH_LEVEL, &patch);
    if (status != CUDSS_STATUS_SUCCESS) {
        printf("cuDSS API error: %d\n", status);
        return 1;
    }
    printf("cuDSS version: %d.%d.%d\n", major, minor, patch);
}
