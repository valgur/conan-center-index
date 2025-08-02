#include <nvJitLink.h>
#include <stdio.h>

int main() {
    unsigned int major, minor;
    nvJitLinkResult status = nvJitLinkVersion(&major, &minor);
    if (status != NVJITLINK_SUCCESS) {
        printf("nvJitLink API error: %d\n", status);
        return 1;
    }
    printf("nvJitLink version: %d.%d\n", major, minor);
}
