#include <nvvm.h>
#include <stdio.h>

int main() {
    int major, minor;
    nvvmResult status = nvvmVersion(&major, &minor);
    if (status != NVVM_SUCCESS) {
        printf("nvvmVersion failed with error code: %d\n", status);
        return 1;
    }
    printf("NVVM Version: %d.%d\n", major, minor);
}
