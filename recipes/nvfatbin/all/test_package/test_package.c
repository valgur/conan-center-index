#include <nvFatbin.h>
#include <stdio.h>

int main() {
    unsigned int major, minor;
    nvFatbinResult status = nvFatbinVersion(&major, &minor);
    if (status != NVFATBIN_SUCCESS) {
        printf("nvFatbin API error: %d\n", status);
        return 1;
    }
    printf("nvFatbin version: %d.%d\n", major, minor);
}
