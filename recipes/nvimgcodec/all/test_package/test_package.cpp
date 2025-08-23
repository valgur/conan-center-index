#include <nvimgcodec.h>
#include <stdio.h>

int main() {
    nvimgcodecProperties_t properties;
    properties.struct_type = NVIMGCODEC_STRUCTURE_TYPE_PROPERTIES;
    nvimgcodecStatus_t status = nvimgcodecGetProperties(&properties);
    if (status != NVIMGCODEC_STATUS_SUCCESS) {
        printf("Failed to get properties: %d\n", status);
        return 1;
    }
    int major = properties.version / 1000;
    int minor = (properties.version % 1000) / 100;
    int patch = properties.version % 100;
    printf("nvImageCodec version: %d.%d.%d\n", major, minor, patch);
}
