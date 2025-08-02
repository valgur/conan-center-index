#include <nvml.h>
#include <stdio.h>

int main() {
    char version[100];
    nvmlReturn_t status = nvmlSystemGetNVMLVersion(version, sizeof(version));
    if (status != NVML_SUCCESS) {
        printf("NVML API error: %d\n", status);
        return 0;
    }
    printf("NVML version: %s\n", version);
}
