#include <nvrtc.h>
#include <stdio.h>

int main() {
    int major, minor;
    nvrtcResult status = nvrtcVersion(&major, &minor);
    if (status != NVRTC_SUCCESS) {
        printf("NVRTC API error: %d\n", status);
        return 1;
    }
    printf("NVRTC version: %d.%d\n", major, minor);
}
