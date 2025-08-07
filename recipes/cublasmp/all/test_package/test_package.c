#include <cublasmp.h>
#include <stdio.h>

int main() {
    int version;
    cublasMpStatus_t status = cublasMpGetVersion(&version);
    if (status != CUBLASMP_STATUS_SUCCESS) {
        printf("cuBLASMp API error: %d\n", status);
        return 1;
    }
    int major = version / 1000;
    int minor = version % 1000 / 100;
    int patch = version % 100;
    printf("cuBLASMp version: %d.%d.%d\n", major, minor, patch);
}
