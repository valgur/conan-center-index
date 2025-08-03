#include <nvjpeg2k.h>
#include <stdio.h>

int main() {
    nvjpeg2kStatus_t status = NVJPEG2K_STATUS_SUCCESS;
    int major, minor, patch;
    status |= nvjpeg2kGetProperty(MAJOR_VERSION, &major);
    status |= nvjpeg2kGetProperty(MINOR_VERSION, &minor);
    status |= nvjpeg2kGetProperty(PATCH_LEVEL, &patch);
    if (status != NVJPEG2K_STATUS_SUCCESS) {
        printf("nvJPEG2000 API error: %d\n", status);
        return 1;
    }
    printf("nvJPEG2000 version: %d.%d.%d\n", major, minor, patch);
}
