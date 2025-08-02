#include <nvjpeg.h>
#include <stdio.h>

int main() {
    nvjpegStatus_t status = NVJPEG_STATUS_SUCCESS;
    int major, minor, patch;
    status |= nvjpegGetProperty(MAJOR_VERSION, &major);
    status |= nvjpegGetProperty(MINOR_VERSION, &minor);
    status |= nvjpegGetProperty(PATCH_LEVEL, &patch);
    if (status != NVJPEG_STATUS_SUCCESS) {
        printf("nvJPEG API error: %d\n", status);
        return 1;
    }
    printf("nvJPEG version: %d.%d.%d\n", major, minor, patch);
}
